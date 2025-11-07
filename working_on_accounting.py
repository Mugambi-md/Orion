from datetime import date

def check_account_name_exists(conn, prefix):
    try:
        keyword = f"{prefix}%"
        with conn.cursor() as cursor:
            cursor.execute("""
                    SELECT account_name FROM chart_of_accounts
                    WHERE account_name LIKE %s
                    """, (keyword,))
            return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        return f"Error checking account name: {str(e)}"

def insert_account(conn, account_name, account_type, code, description):
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            INSERT INTO chart_of_accounts (account_name, account_type, code, description)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                account_name=VALUES(account_name),
                account_type=VALUES(account_type),
                description=VALUES(description)
            """, (account_name, account_type, code, description))
        conn.commit()
        return f"Account '{account_name}' inserted/updated successfully."
    except Exception as e:
        conn.rollback()
        return f"Error inserting account: {str(e)}"

def count_accounts_by_type(conn, account_type):
    """Returns the number of accounts for the given account_type.
    E.g: Asset, Liability, Equity, Revenue and Expense."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT COUNT(*) FROM chart_of_accounts
            WHERE account_type = %s;
            """, (account_type,))
            result = cursor.fetchone()
            return result[0] if result else 0
    except Exception as e:
        return f"Error counting accounts: {str(e)}"

def insert_journal_entry(conn, reference_no, line_items):
    """Insert a journal entry and its associated lines. Returns a success message or error message"""
    try:
        with conn.cursor() as cursor:
            today = date.today()
            # Insert into journal entries
            cursor.execute("""
                    INSERT INTO journal_entries (entry_date, reference_no)
                    VALUES (%s, %s)
                    """, (today, reference_no))
            journal_id = cursor.lastrowid
            # Insert lines
            for line in line_items:
                cursor.execute("""
                INSERT INTO journal_entry_lines (journal_id, account_code,
                    description, debit, credit)
                VALUES (%s, %s, %s, %s, %s)
                """, (
                    journal_id,
                    line['account_code'],
                    line.get('description', ''),
                    line.get('debit', 0.00),
                    line.get('credit', 0.00)
                ))
        conn.commit()
        return True, f"Journal entry #{journal_id} recorded successfully."
    except Exception as e:
        conn.rollback()
        return False, f"Error inserting journal: {str(e)}"

def get_account_name_and_code(conn):
    """Returns a single account dict {'account_name':..., 'code':...} Matching either account name or code."""
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT account_name, code FROM chart_of_accounts"
            )
            return cursor.fetchall()
    except Exception as e:
        return f"Error fetching account: {e}"
def get_account_by_name_or_code(conn, value):
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""
                    SELECT account_name, code FROM chart_of_accounts
                    WHERE account_name=%s OR code=%s
                    LIMIT 1
                    """, (value, value))
            result = cursor.fetchone()
            return result
    except Exception as e:
        print(f"Error fetching account: {str(e)}")
        return None

def fetch_trial_balance(conn):
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM trial_balance")
            results = cursor.fetchall()
            return results
    except Exception as e:
        return f"Error fetching trial balance: {str(e)}"

def get_income_statement(conn):
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM income_statement")
            return True, cursor.fetchall()
    except Exception as e:
        return False, f"Error fetching income statement: {str(e)}"


def insert_opening_balance(conn, opening_lines):
    """Inserts an opening balance journal entry once, Returns (Success, Message)."""
    try:
        with conn.cursor() as cursor:
            # Check if opening balance already exists
            cursor.execute("""
                    SELECT COUNT(*) FROM journal_entries
                    WHERE reference_no LIKE 'OB-%'
                    """)
            (existing_count,) = cursor.fetchone()
            if existing_count > 0:
                return False, "Opening balance already recorded. Cannot insert again."
            # Insert new opening balance journal
            today = date.today()
            ref = f"OB-{today.year}"
            cursor.execute("""
                    INSERT INTO journal_entries (entry_date, reference_no)
                    VALUES (%s, %s)
                    """, (today, ref))
            journal_id = cursor.lastrowid
            for line in opening_lines:
                cursor.execute("""
                        INSERT INTO journal_entry_lines (journal_id, account_code, description, debit, credit)
                        VALUES (%s, %s, %s, %s, %s)
                        """, (
                    journal_id,
                    line["account_code"],
                    line.get("description", "Opening Balance"),
                    line.get("debit", 0.00),
                    line.get("credit", 0.00)
                ))
        conn.commit()
        return True, f"Opening balance Journal #{journal_id} recorded successfully."
    except Exception as e:
        conn.rollback()
        return False, f"Error inserting opening balance: {str(e)}"

def fetch_chart_of_accounts(conn):
    """Fetch account name, account type, code and description from chart of accounts table.
    Returns a list of dictionaries."""
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""
                    SELECT account_name, account_type, code, description
                    FROM chart_of_accounts
                    ORDER BY code;
                    """)
            accounts = cursor.fetchall()
            return accounts, []
    except Exception as e:
        return f"Error fetching chart of accounts: {str(e)}", []

def fetch_journal_lines_by_account_code(conn, account_code):
    """Fetch journal account and account name for specific account code."""
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT
                    jel.journal_id,
                    jel.account_code,
                    coa.account_name,
                    jel.description,
                    jel.debit,
                    jel.credit
                FROM journal_entry_lines jel
                JOIN chart_of_accounts coa ON jel.account_code = coa.code
                WHERE jel.account_code=%s
                """, (account_code,))
            results = cursor.fetchall()
            return results
    except Exception as e:
        return f"Error fetching journal lines: {str(e)}"

def reverse_journal_entry(conn, original_journal_id):
    """Reverses a journal entry by inserting a new entry with opposite
    debit/ credit values."""
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT jel.account_code, jel.description, jel.debit, jel.credit, je.reference_no
                FROM journal_entry_lines jel
                JOIN journal_entries je ON jel.journal_id = je.journal_id
                WHERE jel.journal_id=%s
                """, (original_journal_id,))
            original_lines = cursor.fetchall()
            if not original_lines:
                return f"No journal found for journal ID {original_journal_id}."
            # Create reversal entry
            today = date.today()
            reversal_reference = f"Reversal of #{original_journal_id}"
            cursor.execute("""
                INSERT INTO journal_entries (entry_date, reference_no)
                VALUES (%s, %s)
                """, (today, reversal_reference))
            new_journal_id = cursor.lastrowid
            for line in original_lines:
                cursor.execute("""
                    INSERT INTO journal_entry_lines (journal_id, account_code,
                        description, debit, credit)
                    VALUES (%s, %s, %s, %s, %s)
                    """, (
                    new_journal_id,
                    line["account_code"],
                    f"Reversal: {line['description']}",
                    line["credit"], # Reversed
                    line["debit"] # Reversed
                ))
        conn.commit()
        return True, f"Reversed journal successfully for original ID #{original_journal_id}."
    except Exception as e:
        conn.rollback()
        return False, f"Error reversing journal entry: {str(e)}."

def fetch_all_journal_lines_with_names(conn):
    """Fetch all journal entries with account name joining chart of accounts."""
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT
                    je.entry_date,
                    jel.journal_id,
                    jel.account_code,
                    coa.account_name,
                    jel.description,
                    jel.debit,
                    jel.credit
                FROM journal_entry_lines jel
                JOIN chart_of_accounts coa ON jel.account_code = coa.code
                JOIN journal_entries je ON jel.journal_id = je.journal_id
                ORDER BY je.entry_date ASC, jel.journal_id ASC;
                """)
            return cursor.fetchall()
    except Exception as e:
        return f"Error fetching journal accounts: {str(e)}."

class CashFlowStatement:
    def __init__(self, conn):
        self.conn = conn

    def get_cash_flow_statement(self):
        try:
            with self.conn.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT * FROM cash_flow_statement")
                rows = cursor.fetchall()
                inflows = []
                outflows = []
                for row in rows:
                    account = row['account_name'].lower()
                    if 'depreciation' in account:
                        continue
                    amount = row['amount']
                    category = row['category']
                    account_code = row['account_code']
                    account_name = row['account_name']
                    entry = {
                        "category": category,
                        "account_code": account_code,
                        "account_name": account_name,
                        "amount": round(amount, 2)
                    }
                    if amount > 0:
                        inflows.append(entry)
                    elif amount < 0:
                        outflows.append(entry)
                return {
                    "cash_inflows": inflows,
                    "cash_outflows": outflows
                }
        except Exception as e:
            return f"Error fetching cash flow statement: {str(e)}"

def get_balance_sheet(conn):
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM balance_sheet")
            rows = cursor.fetchall()
            assets = []
            liabilities = []
            equity = []
            total_assets = 0.00
            total_liabilities = 0.00
            total_equity = 0.00
            for row in rows:
                amount = float(row["amount"] or 0.00)
                amount = round(amount, 2)
                entry = {
                    "category": row["category"],
                    "account_code": row["account_code"],
                    "account_name": row["account_name"],
                    "amount": amount
                }
                category = row["category"].lower()
                if category == "asset":
                    assets.append(entry)
                    total_assets += amount
                elif category == "liability":
                    liabilities.append(entry)
                    total_liabilities += amount
                elif category == "equity":
                    equity.append(entry)
                    total_equity += amount
            # Sort each category by account_code
            assets.sort(key=lambda x: x["account_code"])
            equity.sort(key=lambda x: x["account_code"])
            liabilities.sort(key=lambda x: x["account_code"])
            return {
                "assets": {
                    "items": assets,
                    "total": round(total_assets, 2)
                },
                "liabilities": {
                    "items": liabilities,
                    "total": round(total_liabilities, 2)
                },
                "equity": {
                    "items": equity,
                    "total": round(total_equity, 2)
                }
            }
    except Exception as e:
        return f"Error fetching balance sheet: {str(e)}"

def delete_journal_entry(conn, journal_id):
    try:
        with conn.cursor() as cursor:
            # Delete related journal entry lines first
            cursor.execute("""
                DELETE FROM journal_entry_lines
                WHERE journal_id = %s
                """, (journal_id,))
            # Delete the main journal entry
            cursor.execute("""
                DELETE FROM journal_entries
                WHERE journal_id = %s
                """, (journal_id,))
        conn.commit()
        return f"Journal entry {journal_id} deleted successfully."
    except Exception as e:
        conn.rollback()
        return f"Error deleting journal entry: {str(e)}"


class SalesJournalRecorder:
    PREFIX_MAP = {
        "Asset": 1,
        "Liability": 2,
        "Equity": 3,
        "Revenue": 4,
        "Expense": 5
    }
    def __init__(self, conn):
        """Initialize with a Mysql connection."""
        self.conn = conn
    def ensure_accounts_exist(self, account_details):
        """
        Ensure all accounts in account_details exist in chart of accounts.
        Returns dict {account_name: account_code}.
        """
        account_codes = {}
        try:
            for name, info in account_details.items():
                # 1. Check if account exists by name
                result = get_account_by_name_or_code(self.conn, name)
                if result:
                    # Account exists
                    account_codes[name] = result["code"]
                else:
                    # 2. Count existing accounts by type
                    account_type = info["type"]
                    count = count_accounts_by_type(self.conn, account_type)
                    # 3. Generate account code
                    prefix = self.PREFIX_MAP.get(account_type, 9)
                    code = int(f"{prefix * 10}{count + 1:03d}")
                    # Insert new account
                    descr = info.get("description", "")
                    insert_account(self.conn, name, account_type, code, descr)
                    # store code for later use
                    account_codes[name] = code
            return True, account_codes
        except Exception as e:
            return  False, f"Error: {str(e)}"

    def create_journal_entry(self, reference_no):
        """Create a new journal entry and return its ID or None if failed."""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                INSERT INTO journal_entries (entry_date, reference_no)
                VALUES (%s, %s)
                """, (date.today(), reference_no))
                last_id = cursor.lastrowid
                self.conn.commit()
            return True, last_id
        except Exception as e:
            return False, str(e)

    def insert_journal_lines(self, journal_id, lines, account_codes):
        """Insert debit and credit lines into journal_entry_lines."""
        try:
            with self.conn.cursor() as cursor:
                for line in lines:
                    acc_name = line["account_name"]
                    account_code = account_codes.get(acc_name)
                    if not account_code:
                        raise ValueError(f"Acc Code of  {acc_name} not found")
                    cursor.execute("""
                    INSERT INTO journal_entry_lines(journal_id, account_code,
                        description, debit, credit)
                    VALUES (%s, %s, %s, %s, %s)
                    """, (
                        journal_id,
                        account_code,
                        line.get("description", ""),
                        line.get("debit", 0.00),
                        line.get("credit", 0.00)
                    ))
                self.conn.commit()
                return True, "Journal Recorded Successfully."
        except Exception as e:
            self.conn.rollback()
            return False, f"Error: {str(e)}."

    def record_sales(self, account_details, transaction_lines, reference_no):
        """Records a sales transaction.
        Returns True if successful, False otherwise."""
        try:
            # Ensure accounts exists
            ok, result = self.ensure_accounts_exist(account_details)
            if not ok:
                return False, result
            codes = result
            # 2. Create journal entry
            ok, journal_result = self.create_journal_entry(reference_no)
            if not ok:
                return False, journal_result
            journal_id = journal_result
            # 3. Insert journal lines
            ok, msg = self.insert_journal_lines(journal_id, transaction_lines, codes)
            if not ok:
                return False, msg
            return True, "Sales transaction recorded successfully."
        except Exception as e:
            self.conn.rollback()
            return False, f"Error: {str(e)}"
