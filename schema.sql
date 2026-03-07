-- ──────────────────────────────────────────────
-- Categories
-- ──────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='categories' AND xtype='U')
CREATE TABLE categories (
    id       INT           PRIMARY KEY IDENTITY(1,1),
    name     NVARCHAR(100) NOT NULL UNIQUE,
    color    NVARCHAR(7)   NOT NULL DEFAULT '#4A90D9'
);

-- ──────────────────────────────────────────────
-- Transactions
-- ──────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='transactions' AND xtype='U')
CREATE TABLE transactions (
    id          INT           PRIMARY KEY IDENTITY(1,1),
    amount      DECIMAL(10,2) NOT NULL,
    type        NVARCHAR(7)   NOT NULL CHECK(type IN ('income', 'expense')),
    description NVARCHAR(255) NULL,
    category_id INT           NULL,
    date        DATE          NOT NULL DEFAULT CAST(GETDATE() AS DATE),
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- ──────────────────────────────────────────────
-- Budgets
-- ──────────────────────────────────────────────
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='budgets' AND xtype='U')
CREATE TABLE budgets (
    id            INT           PRIMARY KEY IDENTITY(1,1),
    category_id   INT           NOT NULL UNIQUE,
    monthly_limit DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- ──────────────────────────────────────────────
-- Seed default categories (only if table is empty)
-- ──────────────────────────────────────────────
IF NOT EXISTS (SELECT 1 FROM categories)
BEGIN
    INSERT INTO categories (name, color) VALUES
        ('Housing',       '#E74C3C'),
        ('Food',          '#E67E22'),
        ('Transport',     '#F1C40F'),
        ('Health',        '#2ECC71'),
        ('Shopping',      '#9B59B6'),
        ('Entertainment', '#3498DB'),
        ('Salary',        '#1ABC9C'),
        ('Other',         '#95A5A6');
END