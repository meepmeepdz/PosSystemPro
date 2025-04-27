-- Schema for POS system database

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    last_login TIMESTAMP
);

-- Categories table
CREATE TABLE IF NOT EXISTS categories (
    category_id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    parent_id VARCHAR(36),
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    FOREIGN KEY (parent_id) REFERENCES categories(category_id)
);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    sku VARCHAR(50) UNIQUE NOT NULL,
    barcode VARCHAR(50) UNIQUE,
    category_id VARCHAR(36) NOT NULL,
    description TEXT,
    purchase_price NUMERIC(10, 2) NOT NULL,
    selling_price NUMERIC(10, 2) NOT NULL,
    tax_rate NUMERIC(5, 2) NOT NULL DEFAULT 0,
    low_stock_threshold INTEGER NOT NULL DEFAULT 10,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);

-- Stock table
CREATE TABLE IF NOT EXISTS stock (
    stock_id VARCHAR(36) PRIMARY KEY,
    product_id VARCHAR(36) UNIQUE NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Stock movements table
CREATE TABLE IF NOT EXISTS stock_movements (
    movement_id VARCHAR(36) PRIMARY KEY,
    product_id VARCHAR(36) NOT NULL,
    quantity INTEGER NOT NULL,
    movement_type VARCHAR(10) NOT NULL,
    reason TEXT,
    reference_id VARCHAR(36),
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(36) PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20),
    address TEXT,
    tax_id VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

-- Invoices table
CREATE TABLE IF NOT EXISTS invoices (
    invoice_id VARCHAR(36) PRIMARY KEY,
    invoice_number VARCHAR(20) UNIQUE NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    customer_id VARCHAR(36),
    total_amount NUMERIC(10, 2) NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Invoice items table
CREATE TABLE IF NOT EXISTS invoice_items (
    invoice_item_id VARCHAR(36) PRIMARY KEY,
    invoice_id VARCHAR(36) NOT NULL,
    product_id VARCHAR(36) NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL,
    discount_price NUMERIC(10, 2),
    subtotal NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Cash registers table
CREATE TABLE IF NOT EXISTS cash_registers (
    register_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    opening_amount NUMERIC(10, 2) NOT NULL,
    current_amount NUMERIC(10, 2) NOT NULL,
    closing_amount NUMERIC(10, 2),
    opening_time TIMESTAMP NOT NULL,
    closing_time TIMESTAMP,
    status VARCHAR(20) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Cash register transactions table
CREATE TABLE IF NOT EXISTS cash_register_transactions (
    transaction_id VARCHAR(36) PRIMARY KEY,
    register_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    transaction_type VARCHAR(20) NOT NULL,
    description TEXT,
    reference_id VARCHAR(36),
    previous_amount NUMERIC(10, 2) NOT NULL,
    new_amount NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (register_id) REFERENCES cash_registers(register_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Payments table
CREATE TABLE IF NOT EXISTS payments (
    payment_id VARCHAR(36) PRIMARY KEY,
    invoice_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    payment_method VARCHAR(20) NOT NULL,
    reference_number VARCHAR(50),
    payment_date TIMESTAMP NOT NULL,
    notes TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Customer debts table
CREATE TABLE IF NOT EXISTS customer_debts (
    debt_id VARCHAR(36) PRIMARY KEY,
    customer_id VARCHAR(36) NOT NULL,
    invoice_id VARCHAR(36) NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    amount_paid NUMERIC(10, 2) NOT NULL DEFAULT 0,
    is_paid BOOLEAN NOT NULL DEFAULT FALSE,
    created_by VARCHAR(36),
    notes TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    last_payment_date TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

-- Backups table
CREATE TABLE IF NOT EXISTS backups (
    backup_id VARCHAR(36) PRIMARY KEY,
    backup_name VARCHAR(100) NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL,
    is_compressed BOOLEAN NOT NULL DEFAULT FALSE,
    description TEXT,
    created_at TIMESTAMP NOT NULL
);

-- Restore logs table
CREATE TABLE IF NOT EXISTS restore_logs (
    restore_id VARCHAR(36) PRIMARY KEY,
    backup_id VARCHAR(36) NOT NULL,
    status VARCHAR(20) NOT NULL,
    message TEXT,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (backup_id) REFERENCES backups(backup_id)
);