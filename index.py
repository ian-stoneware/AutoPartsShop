from flask import Flask, render_template, redirect, url_for, session, flash, send_file, jsonify, request
from db import db
from itertools import groupby
from operator import attrgetter
import os
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from user import User
from product import Product
from order import Order
from administrator import Administrator
from operatingspecialist import OperatingSpecialist
from math import ceil

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Config
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:65857184@localhost/autopart'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Routes
@app.route('/', methods=['GET', 'POST'])
def index():
    user = None
    user_profile = None
    orders = []

    if 'user_id' in session:
        user = User.query.get(session['user_id'])

    if request.method == 'POST':
        if user:
            new_password = request.form.get('new_password')
            if new_password:
                if User.reset_password(user.name, user.email, new_password):
                    flash("Password reset successful!")
                else:
                    flash("Failed! Please use a new password different from your current password.")
            else:
                flash("Password missing.")
            return redirect(url_for('index'))
        else:
            flash("You must be logged in to reset your password.")
            return redirect(url_for('login'))

    if user:
        user_profile = {
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'userId': user.userId
        }
        session['username'] = user.name
        orders = Order.query.filter_by(userId=user.userId).order_by(Order.date.desc()).all()

    products = Product.query.order_by(Product.brand, Product.model).all()
    grouped_products = {}
    for brand, brand_group in groupby(products, key=attrgetter('brand')):
        brand_group_list = list(brand_group)
        models = {}
        for model, model_group in groupby(brand_group_list, key=attrgetter('model')):
            models[model] = list(model_group)
        grouped_products[brand] = models

    return render_template(
        'index.html',
        grouped_products=grouped_products,
        user=user_profile,
        orders=orders
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.login(username, password)
        if user:
            session['user_id'] = user.userId
            session['username'] = user.name
            if user.role == 'administrator':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'operating specialist':
                return redirect(url_for('ops_dashboard'))
            else:
                return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        if User.register(name, email, password):
            return redirect(url_for('login'))
        else:
            return render_template('register.html', error='User already exists')

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Remove user ID from session
    session.pop('username', None)  # Remove username from session (optional)
    return redirect(url_for('index'))  # Redirect to the home page after logout

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    admin = User.query.get(session['user_id'])
    if admin.role != 'administrator':
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for('index'))

    # Get the current page from the URL, default to 1 if not present
    page = request.args.get('page', 1, type=int)

    # Define how many users per page
    users_per_page = 10

    # Get users for the current page, with pagination
    users = User.query.paginate(page=page, per_page=users_per_page, error_out=False)

    # Calculate total pages
    total_pages = users.pages

    return render_template('admin_dashboard.html', users=users.items, page=page, total_pages=total_pages)

@app.route('/add_user', methods=['POST'])
def add_user():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if user.role != 'administrator':
        return redirect(url_for('index'))

    administrator = Administrator(user)

    user_data = {
        "name": request.form['name'],
        "email": request.form['email'],
        "password": request.form.get('password'),
        "role": request.form.get('role')
    }
    administrator.add_user(**user_data)
    return redirect(url_for('admin_dashboard'))

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if user.role != 'administrator':
        return redirect(url_for('index'))

    administrator = Administrator(user)
    administrator.delete_user(user_id)
    return redirect(url_for('admin_dashboard'))

@app.route('/update_user/<int:user_id>', methods=['POST'])
def update_user(user_id):
    # Check if the user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Get the current user (the admin)
    user = User.query.get(session['user_id'])

    # Check if the user is an administrator
    if user.role != 'administrator':
        return redirect(url_for('index'))

    # Initialize the Administrator class
    administrator = Administrator(user)

    # Get form data
    name = request.form.get('name')
    email = request.form.get('email')

    # Prepare the update fields (only update the fields that are provided)
    kwargs = {}
    if name:
        kwargs['name'] = name
    if email:
        kwargs['email'] = email

    # Perform the update operation
    if kwargs:
        administrator.update_user(user_id, **kwargs)

    return redirect(url_for('admin_dashboard'))

@app.route('/grant_role/<int:user_id>', methods=['POST'])
def grant_role(user_id):
    from administrator import Administrator

    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if user.role != 'administrator':
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for('index'))

    try:
        admin = Administrator(user)
        admin.grant_privileges(user_id, "operating specialist")
        flash("Role granted successfully.", "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for('admin_dashboard'))

@app.route('/deprive_role/<int:user_id>', methods=['POST'])
def deprive_role(user_id):
    from administrator import Administrator

    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if user.role != 'administrator':
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for('index'))

    try:
        admin = Administrator(user)
        admin.grant_privileges(user_id, "customer")
        flash("Role removed successfully.", "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for('admin_dashboard'))



@app.route('/ops_dashboard')
def ops_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if user.role != 'operating specialist':
        return redirect(url_for('index'))

    # Pagination parameters from query string
    product_page = request.args.get('product_page', 1, type=int)
    order_page = request.args.get('order_page', 1, type=int)
    per_page = 10

    # All products and orders (for count only)
    total_products = Product.query.count()
    total_orders = Order.query.count()

    # Paginated query
    products = Product.query.offset((product_page - 1) * per_page).limit(per_page).all()
    orders = Order.query.order_by(Order.date.desc()).offset((order_page - 1) * per_page).limit(per_page).all()

    product_total_pages = ceil(total_products / per_page)
    order_total_pages = ceil(total_orders / per_page)

    return render_template('ops_dashboard.html',
                           user=user,
                           products=products,
                           orders=orders,
                           product_page=product_page,
                           order_page=order_page,
                           product_total_pages=product_total_pages,
                           order_total_pages=order_total_pages)

@app.route('/add_product', methods=['POST'])
def add_product():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if user.role != 'operating specialist':
        return redirect(url_for('index'))

    specialist = OperatingSpecialist(user)

    product_data = {
        "productName": request.form['productName'],
        "description": request.form['description'],
        "price": float(request.form['price']),
        "stock": int(request.form['stock']),
        "category": request.form.get('category'),
        "brand": request.form.get('brand'),
        "model": request.form.get('model')
    }
    specialist.add_product(**product_data)
    return redirect(url_for('ops_dashboard'))

@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if user.role != 'operating specialist':
        return redirect(url_for('index'))

    specialist = OperatingSpecialist(user)
    specialist.delete_product(product_id)
    return redirect(url_for('ops_dashboard'))

@app.route('/update_product/<int:product_id>', methods=['POST'])
def update_product(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if user.role != 'operating specialist':
        return redirect(url_for('index'))

    specialist = OperatingSpecialist(user)

    price = request.form.get('price')
    stock = request.form.get('stock')

    kwargs = {}
    if price:
        kwargs['price'] = float(price)
    if stock:
        kwargs['stock'] = int(stock)

    specialist.update_product(product_id, **kwargs)
    return redirect(url_for('ops_dashboard'))

@app.route('/process_order/<int:order_id>', methods=['POST'])
def process_order(order_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if user.role != 'operating specialist':
        return redirect(url_for('index'))

    specialist = OperatingSpecialist(user)
    specialist.process_order(order_id)
    return redirect(url_for('ops_dashboard'))

@app.route('/checkout', methods=['POST'])
def checkout():
    from customer import Customer
    if 'user_id' not in session:
        return jsonify({'message': 'User not logged in'}), 401

    data = request.get_json()
    product_ids = [item['id'] for item in data.get('cart', [])]

    if not product_ids:
        return jsonify({'message': 'Cart is empty'}), 400

    user = User.query.get(session['user_id'])

    try:
        customer = Customer(user)
        customer.make_order(product_ids)
        # Return JSON success response, no redirect
        return jsonify({'message': 'Order placed successfully'})
    except Exception as e:
        return jsonify({'message': f'Checkout failed: {str(e)}'}), 500

@app.route('/payment/<int:order_id>', methods=['POST'])
def payment(order_id):
    from customer import Customer

    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    customer = Customer(user)

    payment_method = request.form.get('payment_method')  # 'wechat', 'alipay', 'stripe'
    print("Selected payment method:", payment_method)

    try:
        # Call your payment logic
        payment_result = customer.make_payment(order_id, payment_method)
        print("Payment result:", payment_result)  # Debugging

        # Update order status
        order = Order.query.get(order_id)
        order.payMethod = payment_method

        if payment_result == 'success':
            order.status = 'paid'
        else:
            order.status = 'payment_failed'
            flash("Payment failed or was canceled.", "danger")

        db.session.commit()

        # Redirect or render depending on payment method
        if payment_method == 'wechat':
            return redirect(url_for('wechat_pay', order_id=order_id, method=payment_method))
        elif payment_method == 'alipay':
            return redirect(url_for('alipay', order_id=order_id, method=payment_method))
        elif payment_method == 'credit_card':
            return redirect(url_for('credit_card_pay', order_id=order_id, method=payment_method))

        else:
            flash("Unsupported payment method", "danger")
            return redirect(url_for('payment_result', status='failure'))

    except Exception as e:
        print("Payment error:", e)
        import traceback
        traceback.print_exc()
        return redirect(url_for('payment_result', status='failure'))
@app.route('/payment_result', methods=['GET'])
def payment_result():
    status = request.args.get('status')
    order_id = request.args.get('order_id')

    if not order_id:
        return jsonify({'success': False, 'message': 'Missing order ID'}), 400

    order = Order.query.get(order_id)
    if not order:
        return jsonify({'success': False, 'message': 'Order not found'}), 404

    if status == 'success':
        order.status = 'paid'
        message = "Payment was successful!"
    elif status == 'failure':
        order.status = 'payment_failed'
        message = "Payment was canceled."
    else:
        return jsonify({'success': False, 'message': 'Unknown status'}), 400

    db.session.commit()

    return jsonify({'success': True, 'message': message, 'order_status': order.status})

@app.route('/cancel_order/<int:order_id>', methods=['POST'])
def cancel_order(order_id):
    from customer import Customer

    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    try:
        customer = Customer(user)
        customer.cancel_order(order_id)
        flash(f"Order {order_id} cancelled.", "success")
    except Exception as e:
        flash(f"Failed to cancel order: {e}", "danger")

    return redirect(url_for('index'))

@app.route('/download_receipt/<int:order_id>')
def download_receipt(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        return "Order not found", 404

    # Compute subtotal and tax
    subtotal = sum(product.price for product in order.productList)
    tax_rate = 0.08
    tax = subtotal * tax_rate
    total = subtotal + tax

    # Load font
    try:
        font = ImageFont.truetype("cour.ttf", 16)
    except:
        font = ImageFont.load_default()

    # Load logo
    try:
        logo = Image.open("static/logo.png").convert("RGBA")
        logo_width = 120
        logo_ratio = logo_width / logo.width
        logo_height = int(logo.height * logo_ratio)
        logo = logo.resize((logo_width, logo_height))
    except:
        logo = None
        logo_height = 0

    padding = 20
    bbox = font.getbbox("A")
    line_height = (bbox[3] - bbox[1]) + 6

    # Receipt lines
    lines = [
        "KEAN UNIVERSITY AUTO PARTS SHOP",
        "88 Daxue Road, Ouhai District, Wenzhou, China",
        "Contact: (0577) 55870115",
        "-" * 40,
        f"Order ID: {order.orderId}",
        f"Date: {order.date.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Customer: {order.userId}",
        f"Payment Method: {order.payMethod}",
        "-" * 40,
        "Products:"
    ]

    for product in order.productList:
        name = product.productName[:25].ljust(25)
        price = f"${product.price:.2f}".rjust(10)
        lines.append(f"{name}{price}")

    lines += [
        "-" * 40,
        f"{'Subtotal'.ljust(30)}{f'${subtotal:.2f}'.rjust(10)}",
        f"{'Tax (8%)'.ljust(30)}{f'${tax:.2f}'.rjust(10)}",
        f"{'Total'.ljust(30)}{f'${total:.2f}'.rjust(10)}",
        "-" * 40,
        "Thank you for shopping!",
        "Visit us again!"
    ]

    # Image dimensions
    width = 280
    text_height = line_height * len(lines)
    height = padding * 2 + logo_height + text_height

    image = Image.new("RGB", (width, height), (245, 245, 245))  # Light gray background
    draw = ImageDraw.Draw(image)

    # Paste logo
    if logo:
        image.paste(logo, ((width - logo_width) // 2, padding), mask=logo)
    text_start_y = padding + logo_height + 10

    # Draw text
    for i, line in enumerate(lines):
        draw.text((padding, text_start_y + i * line_height), line, fill="black", font=font)

    # Save and send
    img_io = BytesIO()
    image.save(img_io, format='PNG')
    img_io.seek(0)

    return send_file(
        img_io,
        mimetype='image/png',
        as_attachment=True,
        download_name=f'receipt_{order.orderId}.png'
    )



# Run
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

