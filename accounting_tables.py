from connect_to_db import connect_db

def create_accounting_tables(conn):
    try:
        with conn.cursor() as cursor:
            # 1. Chart of Accounts
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chart_of_accounts (
                    account_id INT PRIMARY KEY AUTO_INCREMENT,
                    account_name VARCHAR(50) NOT NULL,
                    account_type ENUM('Asset', 'Liability', 'Equity', 'Revenue', 'Expense') NOT NULL,
                    code VARCHAR(20) UNIQUE NOT NULL,
                    description TEXT
                );
                """)
            # 2. Journal Entries
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS journal_entries (
                    journal_id INT PRIMARY KEY AUTO_INCREMENT,
                    entry_date DATE NOT NULL,
                    reference_no VARCHAR(50)
                );
                """)
            # 3. Journal Entry Lines
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS journal_entry_lines(
                line_id INT PRIMARY KEY AUTO_INCREMENT,
                journal_id INT,
                account_code VARCHAR(20),
                description TEXT,
                debit DECIMAL(12, 2) DEFAULT 0.00,
                credit DECIMAL(12, 2) DEFAULT 0.00,
                FOREIGN KEY (journal_id) REFERENCES journal_entries(journal_id),
                FOREIGN KEY (account_code) REFERENCES chart_of_accounts(code)
            );
            """)
            print("Tables created successfully.")
            # 4. Create trial balance view
            cursor.execute("""
                CREATE OR REPLACE VIEW trial_balance AS
                SELECT
                    a.code,
                    a.account_name,
                    a.account_type,
                    SUM(l.debit) AS total_debit,
                    SUM(l.credit) AS total_credit,
                    SUM(l.debit - l.credit) AS balance
                FROM chart_of_accounts a
                LEFT JOIN journal_entry_lines l ON a.code = l.account_code
                GROUP BY a.code, a.account_name, a.account_type;
                """)
            print("Trial Balance view created successfully.")
            cursor.execute("""
                CREATE OR REPLACE VIEW income_statement AS
                SELECT
                    'Revenue' AS category,
                    a.code AS account_code,
                    a.account_name,
                    COALESCE(SUM(l.credit - l.debit), 0.00) AS amount
                FROM chart_of_accounts a
                LEFT JOIN journal_entry_lines l ON a.code=l.account_code
                WHERE a.account_type='Revenue'
                GROUP BY a.code, a.account_name
                
                UNION ALL
                
                SELECT
                    'Expense' AS category,
                    a.code AS account_code,
                    a.account_name,
                    COALESCE(SUM(l.debit - l.credit), 0.00) AS amount
                FROM chart_of_accounts a
                LEFT JOIN journal_entry_lines l ON a.code=l.account_code
                WHERE a.account_type='Expense'
                GROUP BY a.code, a.account_name;
                """)
            print("Income Statement View Created Successfully.")
            cursor.execute("""
                CREATE OR REPLACE VIEW balance_sheet AS
                SELECT
                    a.account_type AS category,
                    a.code AS account_code,
                    a.account_name,
                    COALESCE(
                        CASE
                            WHEN a.account_type = 'Asset' THEN SUM(l.debit - l.credit)
                            WHEN a.account_type IN ('Liability', 'Equity') THEN SUM(l.credit - l.debit)
                            ELSE 0
                        END, 0.00
                    ) AS amount
                FROM chart_of_accounts a
                LEFT JOIN journal_entry_lines l ON a.code = l.account_code
                WHERE a.account_type IN ('Asset', 'Liability', 'Equity')
                GROUP BY a.account_type, a.code, a.account_name;
                """)
            print("Balance Sheet View Created Successfully.")

            cursor.execute("""
                CREATE OR REPLACE VIEW cash_flow_statement AS
                SELECT
                    'Operating Activity' AS category,
                    a.code AS account_code,
                    a.account_name,
                    CASE
                        WHEN SUM(l.credit - l.debit) >= 0 THEN 'inflow' ELSE 'outflow'
                    END AS cash_flow_type,
                    COALESCE(SUM(l.credit - l.debit), 0.00) AS amount
                FROM chart_of_accounts a
                LEFT JOIN journal_entry_lines l ON a.code = l.account_code
                 -- Remove non-cash
                WHERE a.account_type IN ('Revenue', 'Expense')
                AND account_name NOT LIKE '%Depreciation%'
                GROUP BY a.code, a.account_name
                
                UNION ALL
                
                -- Financing Activities
                SELECT
                    'Financing Activity' AS category,
                    a.code AS account_code,
                    a.account_name,
                    CASE
                        WHEN SUM(l.credit - l.debit) >= 0 THEN 'inflow' ELSE 'outflow'
                    END AS cash_flow_type,
                    COALESCE(SUM(l.credit - l.debit), 0.00) AS amount
                FROM chart_of_accounts a
                LEFT JOIN journal_entry_lines l ON a.code = l.account_code
                WHERE a.account_type IN ('Equity', 'Liability')
                GROUP BY a.code, a.account_name
                
                UNION ALL
                
                -- Investing Activities
                SELECT
                    'Investing Activities' AS category,
                    a.code AS account_code,
                    a.account_name,
                    CASE
                        WHEN SUM(l.credit - l.debit) >= 0 THEN 'inflow' ELSE 'outflow'
                    END AS cash_flow_type,
                    COALESCE(SUM(l.credit - l.debit), 0.00) AS amount
                FROM chart_of_accounts a
                LEFT JOIN journal_entry_lines l ON a.code = l.account_code
                WHERE a.account_type = 'Asset'
                GROUP BY a.code, a.account_name;
                """)
            print("Cash Flow Statement View Created Successfully.")
            cursor.execute("""
                    CREATE TABLE IF NOT EXISTS journal_archive (
                        id INT PRIMARY KEY AUTO_INCREMENT,
                        date DATE,
                        account_code VARCHAR(20),
                        account_name VARCHAR(50),
                        description TEXT,
                        debit DECIMAL(15, 2),
                        credit DECIMAL(15, 2),
                        period_end_year INT,
                        FOREIGN KEY (account_code) REFERENCES chart_of_accounts(code)
                            ON UPDATE CASCADE
                            ON DELETE SET NULL
                    );
                    """)
            print("Table Journal Archive created successfully.")
            cursor.execute("""
                    CREATE TABLE IF NOT EXISTS system_settings(
                        setting_key VARCHAR(50) PRIMARY KEY,
                        setting_value TEXT
                    );
                    """)
            print("System Settings Table created Successfully.")
        conn.commit()
    except Exception as e:
        print("Error creating tables:", str(e))
    finally:
        conn.close()

conn = connect_db()
create_accounting_tables(conn)