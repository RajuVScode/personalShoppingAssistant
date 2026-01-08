from sqlalchemy.orm import Session
from datetime import date
from backend.database.models import Customer, Product, CustomerPreferences, CustomerAddress


def seed_database(db: Session):
    customers = [
        Customer(customer_id="CUST-0000001",
                 first_name="Sarah",
                 last_name="Johnson",
                 email="sarah@example.com",
                 phone_number="+1-212-555-0101",
                 date_of_birth=date(1990, 5, 15),
                 gender="female",
                 preferred_channel="email",
                 marketing_opt_in=True,
                 vip_flag=True,
                 lifetime_value_cents=125000,
                 avg_order_value_cents=25000,
                 total_orders=5,
                 preferred_store_id="NYC001",
                 notes="Prefers modern, minimalist styles",
                 password="password123"),
        Customer(customer_id="CUST-0000002",
                 first_name="Michael",
                 last_name="Chen",
                 email="michael@example.com",
                 phone_number="+1-415-555-0102",
                 date_of_birth=date(1988, 9, 22),
                 gender="male",
                 preferred_channel="sms",
                 marketing_opt_in=True,
                 vip_flag=False,
                 lifetime_value_cents=75000,
                 avg_order_value_cents=15000,
                 total_orders=5,
                 preferred_store_id="SF001",
                 notes="Tech-savvy, loves athleisure",
                 password="password123"),
        Customer(customer_id="CUST-0000003",
                 first_name="Emma",
                 last_name="Williams",
                 email="emma@example.com",
                 phone_number="+1-310-555-0103",
                 date_of_birth=date(1995, 3, 8),
                 gender="female",
                 preferred_channel="email",
                 marketing_opt_in=False,
                 vip_flag=False,
                 lifetime_value_cents=45000,
                 avg_order_value_cents=15000,
                 total_orders=3,
                 preferred_store_id="LA001",
                 notes="Eco-conscious, prefers sustainable brands",
                 password="password123")
    ]

    for customer in customers:
        db.add(customer)

    customer_preferences = [
        CustomerPreferences(
            customer_id="CUST001",
            categories_interested=["dresses", "blazers", "accessories"],
            price_sensitivity="low",
            preferred_brands=["Hugo Boss", "Everlane", "Reformation"],
            preferred_styles=["modern", "minimalist", "professional"],
            preferred_shopping_days="weekends"),
        CustomerPreferences(
            customer_id="CUST002",
            categories_interested=["sneakers", "activewear", "outerwear"],
            price_sensitivity="medium",
            preferred_brands=["Adidas", "Patagonia", "North Face"],
            preferred_styles=["casual", "tech-wear", "athleisure"],
            preferred_shopping_days="evenings"),
        CustomerPreferences(
            customer_id="CUST003",
            categories_interested=[
                "sustainable fashion", "organic cotton", "accessories"
            ],
            price_sensitivity="medium",
            preferred_brands=["Patagonia", "Everlane", "Reformation"],
            preferred_styles=["bohemian", "elegant", "sustainable"],
            preferred_shopping_days="weekends")
    ]

    for pref in customer_preferences:
        db.add(pref)

    customer_addresses = [
        CustomerAddress(address_id="ADDR001",
                        customer_id="CUST001",
                        label="Home",
                        address_line1="123 Park Avenue",
                        address_line2="Apt 15B",
                        city="New York",
                        state="NY",
                        postal_code="10022",
                        country="USA",
                        is_default_shipping=True,
                        is_default_billing=True),
        CustomerAddress(address_id="ADDR002",
                        customer_id="CUST002",
                        label="Home",
                        address_line1="456 Market Street",
                        address_line2="Suite 200",
                        city="San Francisco",
                        state="CA",
                        postal_code="94102",
                        country="USA",
                        is_default_shipping=True,
                        is_default_billing=True),
        CustomerAddress(address_id="ADDR003",
                        customer_id="CUST003",
                        label="Home",
                        address_line1="789 Sunset Blvd",
                        address_line2=None,
                        city="Los Angeles",
                        state="CA",
                        postal_code="90028",
                        country="USA",
                        is_default_shipping=True,
                        is_default_billing=True)
    ]

    for addr in customer_addresses:
        db.add(addr)

    products = [
        Product(
            name="Classic Oxford Shoes",
            description=
            "Premium leather oxford shoes with timeless design. Perfect for business meetings and formal occasions. Features cushioned insole and durable rubber outsole.",
            category="Footwear",
            subcategory="Dress Shoes",
            price=189.99,
            brand="Clarks",
            gender="men",
            sizes_available=["8", "9", "10", "11", "12"],
            colors=["Black", "Brown", "Burgundy"],
            tags=["formal", "leather", "classic", "office", "wedding"],
            image_url=
            "https://images.unsplash.com/photo-1533867617858-e7b97e060509?w=400",
            in_stock=True,
            rating=4.7,
            material="Leather",
            season="all-season",
            care_instructions="Polish regularly, store with shoe trees"),
        Product(
            name="Ultra Boost Running Shoes",
            description=
            "High-performance running shoes with responsive cushioning and breathable mesh upper. Ideal for marathon training and daily runs.",
            category="Footwear",
            subcategory="Running Shoes",
            price=149.99,
            brand="Adidas",
            gender="unisex",
            sizes_available=["6", "7", "8", "9", "10", "11", "12"],
            colors=["White", "Black", "Navy Blue"],
            tags=["running", "athletic", "comfortable", "sports", "gym"],
            image_url=
            "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400",
            in_stock=True,
            rating=4.8,
            material="Mesh/Synthetic",
            season="all-season",
            care_instructions="Wipe clean with damp cloth"),
        Product(
            name="Merino Wool Blazer",
            description=
            "Sophisticated blazer crafted from Italian merino wool. Slim fit design with notched lapels. Perfect for business casual or smart occasions.",
            category="Apparel",
            subcategory="Blazers",
            price=329.99,
            brand="Hugo Boss",
            gender="men",
            sizes_available=["S", "M", "L", "XL"],
            colors=["Navy", "Charcoal", "Black"],
            tags=["professional", "wool", "office", "meeting", "elegant"],
            image_url=
            "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=400",
            in_stock=True,
            rating=4.6,
            material="Merino Wool",
            season="fall/winter",
            care_instructions="Dry clean only"),
        Product(
            name="Cashmere Turtleneck Sweater",
            description=
            "Luxuriously soft 100% cashmere turtleneck. Lightweight yet warm, perfect for layering. Timeless design that elevates any outfit.",
            category="Apparel",
            subcategory="Sweaters",
            price=249.99,
            brand="Everlane",
            gender="women",
            sizes_available=["XS", "S", "M", "L"],
            colors=["Cream", "Black", "Camel", "Burgundy"],
            tags=["cashmere", "luxury", "winter", "cozy", "elegant"],
            image_url=
            "https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=400",
            in_stock=True,
            rating=4.9,
            material="100% Cashmere",
            season="fall/winter",
            care_instructions="Hand wash cold, lay flat to dry"),
        Product(
            name="Leather Crossbody Bag",
            description=
            "Minimalist crossbody bag in genuine Italian leather. Features adjustable strap and multiple compartments. Perfect for everyday use.",
            category="Accessories",
            subcategory="Bags",
            price=175.00,
            brand="Coach",
            gender="women",
            sizes_available=["One Size"],
            colors=["Black", "Tan", "Burgundy"],
            tags=["leather", "everyday", "minimalist", "practical"],
            image_url=
            "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=400",
            in_stock=True,
            rating=4.5,
            material="Italian Leather",
            season="all-season",
            care_instructions="Condition leather regularly"),
        Product(
            name="Waterproof Rain Jacket",
            description=
            "Lightweight, breathable rain jacket with sealed seams and adjustable hood. Packs into its own pocket for easy travel.",
            category="Apparel",
            subcategory="Outerwear",
            price=129.99,
            brand="Patagonia",
            gender="unisex",
            sizes_available=["XS", "S", "M", "L", "XL"],
            colors=["Navy", "Forest Green", "Yellow", "Black"],
            tags=["rain", "waterproof", "outdoor", "travel", "sustainable"],
            image_url=
            "https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=400",
            in_stock=True,
            rating=4.7,
            material="Recycled Nylon",
            season="spring/fall",
            care_instructions="Machine wash cold, tumble dry low"),
        Product(
            name="Slim Fit Chinos",
            description=
            "Classic chino pants in stretch cotton twill. Slim fit with flat front and slant pockets. Versatile for work or weekend.",
            category="Apparel",
            subcategory="Pants",
            price=79.99,
            brand="J.Crew",
            gender="men",
            sizes_available=["28", "30", "32", "34", "36"],
            colors=["Khaki", "Navy", "Olive", "Stone"],
            tags=["casual", "office", "cotton", "versatile"],
            image_url=
            "https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=400",
            in_stock=True,
            rating=4.4,
            material="Cotton Twill",
            season="all-season",
            care_instructions="Machine wash, tumble dry"),
        Product(
            name="Silk Midi Dress",
            description=
            "Elegant silk midi dress with delicate draping and subtle sheen. Features adjustable waist tie and side slit. Perfect for events.",
            category="Apparel",
            subcategory="Dresses",
            price=295.00,
            brand="Reformation",
            gender="women",
            sizes_available=["XS", "S", "M", "L"],
            colors=["Champagne", "Forest Green", "Navy", "Black"],
            tags=["silk", "elegant", "event", "wedding", "special occasion"],
            image_url=
            "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=400",
            in_stock=True,
            rating=4.8,
            material="100% Silk",
            season="spring/summer",
            care_instructions="Dry clean only"),
        Product(
            name="Chunky White Sneakers",
            description=
            "Retro-inspired chunky sneakers with premium leather upper. Platform sole adds height while remaining comfortable all day.",
            category="Footwear",
            subcategory="Sneakers",
            price=119.99,
            brand="New Balance",
            gender="unisex",
            sizes_available=["5", "6", "7", "8", "9", "10", "11"],
            colors=["White", "White/Navy", "White/Green"],
            tags=["trendy", "casual", "comfortable", "street style"],
            image_url=
            "https://images.unsplash.com/photo-1460353581641-37baddab0fa2?w=400",
            in_stock=True,
            rating=4.6,
            material="Leather/Synthetic",
            season="all-season",
            care_instructions="Wipe clean with damp cloth"),
        Product(
            name="Organic Cotton T-Shirt",
            description=
            "Essential t-shirt made from 100% organic cotton. Relaxed fit with crew neck. Sustainably produced with eco-friendly dyes.",
            category="Apparel",
            subcategory="T-Shirts",
            price=35.00,
            brand="Patagonia",
            gender="unisex",
            sizes_available=["XS", "S", "M", "L", "XL", "XXL"],
            colors=["White", "Black", "Gray", "Navy", "Sage"],
            tags=["sustainable", "organic", "casual", "basic", "everyday"],
            image_url=
            "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400",
            in_stock=True,
            rating=4.5,
            material="100% Organic Cotton",
            season="all-season",
            care_instructions="Machine wash cold"),
        Product(
            name="Leather Belt",
            description=
            "Classic leather belt with brushed metal buckle. Full-grain leather that develops beautiful patina over time.",
            category="Accessories",
            subcategory="Belts",
            price=65.00,
            brand="Allen Edmonds",
            gender="men",
            sizes_available=["30", "32", "34", "36", "38", "40"],
            colors=["Black", "Brown", "Tan"],
            tags=["leather", "classic", "formal", "casual", "essential"],
            image_url=
            "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400",
            in_stock=True,
            rating=4.7,
            material="Full-Grain Leather",
            season="all-season",
            care_instructions="Condition leather regularly"),
        Product(
            name="Down Puffer Jacket",
            description=
            "Warm down puffer jacket with water-resistant shell. Packable design with elasticized cuffs and adjustable hem.",
            category="Apparel",
            subcategory="Outerwear",
            price=199.99,
            brand="North Face",
            gender="unisex",
            sizes_available=["S", "M", "L", "XL"],
            colors=["Black", "Navy", "Red", "Olive"],
            tags=["winter", "warm", "down", "packable", "outdoor"],
            image_url=
            "https://images.unsplash.com/photo-1544923246-77307dd628b8?w=400",
            in_stock=True,
            rating=4.8,
            material="Down/Nylon",
            season="winter",
            care_instructions="Machine wash gentle, tumble dry low"),
        Product(
            name="Aviator Sunglasses",
            description=
            "Classic aviator sunglasses with polarized lenses and metal frame. UV400 protection with anti-reflective coating.",
            category="Accessories",
            subcategory="Eyewear",
            price=165.00,
            brand="Ray-Ban",
            gender="unisex",
            sizes_available=["One Size"],
            colors=["Gold/Green", "Silver/Blue", "Black/Gray"],
            tags=["classic", "sunglasses", "summer", "travel", "timeless"],
            image_url=
            "https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=400",
            in_stock=True,
            rating=4.9,
            material="Metal/Glass",
            season="spring/summer",
            care_instructions="Clean with microfiber cloth"),
        Product(
            name="High-Waist Yoga Pants",
            description=
            "Performance yoga pants with four-way stretch and moisture-wicking fabric. High waist with hidden pocket for essentials.",
            category="Apparel",
            subcategory="Activewear",
            price=89.99,
            brand="Lululemon",
            gender="women",
            sizes_available=["XS", "S", "M", "L"],
            colors=["Black", "Navy", "Burgundy", "Forest"],
            tags=["yoga", "gym", "athletic", "comfortable", "stretchy"],
            image_url=
            "https://images.unsplash.com/photo-1506629082955-511b1aa562c8?w=400",
            in_stock=True,
            rating=4.8,
            material="Nylon/Lycra",
            season="all-season",
            care_instructions="Machine wash cold, lay flat to dry"),
        Product(
            name="Canvas Weekender Bag",
            description=
            "Durable canvas weekender with leather trim. Spacious main compartment with interior pockets and detachable shoulder strap.",
            category="Accessories",
            subcategory="Bags",
            price=145.00,
            brand="Herschel",
            gender="unisex",
            sizes_available=["One Size"],
            colors=["Navy", "Gray", "Olive", "Black"],
            tags=["travel", "weekend", "canvas", "carry-on", "durable"],
            image_url=
            "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400",
            in_stock=True,
            rating=4.6,
            material="Canvas/Leather",
            season="all-season",
            care_instructions="Spot clean only")
    ]

    for product in products:
        db.add(product)

    db.commit()
    print(
        f"Seeded {len(customers)} customers, {len(customer_preferences)} preferences, {len(customer_addresses)} addresses, and {len(products)} products"
    )
