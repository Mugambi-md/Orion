from datetime import date
import calendar

class YearEndProcessor:
    def __init__(self, conn):
        self.conn = conn

    def close_year(self, closing_year):
        try:
            cursor = self.conn.cursor()
            # 1. Ensure Retained Earnings Account Exists
            retained_code = "3000"
            retained_name = "Retained Earnings"
            cursor.execute("SELECT * FROM chart_of_accounts WHERE code=%s", (retained_code,))
            if not cursor.fetchone():
                cursor.execute("""
                        INSERT INTO chart_of_accounts(account_name, account_type, code, description)
                        VALUES (%s, %s, %s, %s)
                        """, (retained_name, 'Equity', retained_code, "Year-end retained earnings"))
            # 2. Calculate Balances per Account
            cursor.execute("""
                SELECT
                    l.account_code,
                    a.account_name,
                    a.account_type,
                    SUM(l.debit) AS total_debit,
                    SUM(l.credit) AS total_credit
                FROM journal_entry_lines l
                JOIN chart_of_accounts a ON l.account_code = a.code
                JOIN journal_entries j ON l.journal_id = j.journal_id
                WHERE YEAR(j.entry_date) = %s
                GROUP BY l.account_code
                """, (closing_year,))
            balances = cursor.fetchall()
            # 3. Archive to journal archive
            cursor.execute("""
            INSERT INTO journal_archive (date, account_code, account_name, description, debit, credit, period_end_year)
            SELECT
                j.entry_date,
                l.account_code,
                a.account_name,
                l.description,
                l.debit,
                l.credit,
                %s
            FROM journal_entry_lines l
            JOIN chart_of_accounts a ON l.account_code = a.code
            JOIN journal_entries j ON l.journal_id = j.journal_id
            WHERE YEAR(j.entry_date) = %s
            """, (closing_year, closing_year))
            # 4. Clear existing journal data
            cursor.execute("""
                DELETE FROM journal_entry_lines
                WHERE journal_id IN (SELECT journal_id FROM journal_entries WHERE YEAR(entry_date) = %s)
                """, (closing_year,))
            cursor.execute("DELETE FROM journal_entries WHERE YEAR(entry_date) = %s", (closing_year,))
            # 5. Insert opening balances for Asset, Liability and Equity
            today = date.today()
            cursor.execute("""
                INSERT INTO journal_entries (entry_date, reference_no)
                VALUES (%s, %s)
                """, (today, f"Opening Balance {closing_year + 1}"))
            opening_journal_id = cursor.lastrowid
            retained_earnings = 0
            for account in balances:
                code, name, acc_type, debit, credit = account
                net = (debit or 0) - (credit or 0)
                # For opening only carry forward Assets, Liabilities, Equity
                if acc_type in ('Asset', 'Liability', 'Equity'):
                    if net != 0:
                        if acc_type in ('Asset', 'Expense'):
                            cursor.execute("""
                                INSERT INTO journal_entry_lines (journal_id, account_code, description, debit, credit)
                                VALUES (%s, %s, %s, %s, %s)
                                """,(opening_journal_id, code, f"Opening balance {closing_year+1}", abs(net), 0.00))
                        else:
                            cursor.execute("""
                                INSERT INTO journal_entry_lines (journal_id, account_code, description, debit, credit)
                                VALUES (%s, %s, %s, %s, %s)
                                """, (opening_journal_id, code, f"Opening balance {closing_year+1}", 0.00, abs(net)))
                elif acc_type in ('Revenue', 'Expense'):
                    retained_earnings += net
                # 6. Post Retained Earnings
                if retained_earnings != 0:
                    desc = f"Retained earnings {closing_year}"
                    if retained_earnings > 0:
                        cursor.execute("""
                            INSERT INTO journal_entry_lines (journal_id, account_code, description, debit, credit)
                            VALUES (%s, %s, %s, %s, %s)
                            """, (opening_journal_id, retained_code, desc, 0.00, abs(retained_earnings)))
                    else:
                        cursor.execute("""
                            INSERT INTO journal_entry_lines (journal_id, account_code, description, debit, credit)
                            VALUES (%s, %s, %s, %s, %s)
                            """, (opening_journal_id, retained_code, desc, abs(retained_earnings), 0.00))
                self.conn.commit()
                return f"Year {closing_year} closed successfully. Opening balances set and retained earnings posted."
        except Exception as e:
            self.conn.rollback()
            return f"Year End closing Failed: {str(e)}"

class YearEndReversalManager:
    def __init__(self, conn):
        self.conn = conn
    def reverse_year(self, year):
        try:
            data = self.fetch_archive_data(year)
            if not data:
                return f"No archived data found for year {year}."
            new_journal_id = self.create_new_journal_entry(f"Reversal of year {year}")
            self.restore_journal_entries(new_journal_id, data)
            self.cleanup_year_plus_one(year)
            self.delete_orphan_journal_entries(year + 1)
            self.conn.commit()
            return f"year {year} successfully reversed and restored."
        except Exception as e:
            self.conn.rollback()
            return f"Error reversing year {year}: {str(e)}"
    def fetch_archive_data(self, year):
        with self.conn.cursor(dictionary=True) as cursor:
            # 1. Get all journal_ids for the year
            cursor.execute("""
                SELECT date, account_code, account_name, description, debit, credit
                FROM journal_archive
                WHERE period_end_year = %s
                ORDER BY date ASC
            """, (year,))
            return cursor.fetchall()
    def create_new_journal_entry(self, reference_note):
        with self.conn.cursor() as cursor:
            entry_date = date.today()
            # Create journal entry
            cursor.execute("""
                INSERT INTO journal_entries(entry_date, reference_no)
                VALUES (%s, %s)
                """, (entry_date, reference_note))
            return cursor.lastrowid
    def restore_journal_entries(self, journal_id, entries):
        # Insert each journal line
        with self.conn.cursor() as cursor:
            for row in entries:
                cursor.execute("""
                INSERT INTO journal_entry_lines (journal_id, account_code,
                        description, debit, credit)
                VALUES (%s, %s, %s, %s, %s)
                """, (
                    journal_id,
                    row['account_code'],
                    row['description'],
                    row['debit'],
                    row['credit']
                ))
    def cleanup_year_plus_one(self, year):
        with self.conn.cursor() as cursor:
            next_year = year + 1
            # Delete opening balances
            cursor.execute("""
                DELETE FROM journal_entry_lines
                WHERE description = %s
                """, (f"Opening balance {next_year}",))
            # Delete Retained Earnings or similar entries
            cursor.execute("""
                DELETE FROM journal_entry_lines
                WHERE description = %s
                """, (f"Retained earnings {year}",))
            # Delete journal archive that year
            cursor.execute("""
                DELETE FROM journal_archive
                WHERE period_end_year = %s
                """, (year,))
    def delete_orphan_journal_entries(self, year):
        # Optionally delete the journal entries if they no longer have lines
        with self.conn.cursor() as cursor:
            cursor.execute("""
                SELECT je.journal_id
                FROM journal_entries je
                LEFT JOIN journal_entry_lines jel ON je.journal_id = jel.journal_id
                WHERE YEAR(je.entry_date) = %s
                GROUP BY je.journal_id
                HAVING COUNT(jel.journal_id) = 0
                """, (year,))
            orphan_ids = cursor.fetchall()
            # Delete orphans
            for (journal_id,) in orphan_ids:
                cursor.execute(
                "DELETE FROM journal_entries WHERE journal_id = %s",
                (journal_id,)
                )

def get_available_periods_from_journal_entries(conn):
    """
    Fetch first and last month of the earliest years from journal entries
    where account code != retained earnings.
    Returns list like ["January 2025 - December 2025"]
    """
    retained_code = "3000" # Retained Earnings account code
    try:
        with (conn.cursor() as cursor):
            cursor.execute("""
            SELECT YEAR(j.entry_date) AS year, MONTH(j.entry_date) AS month
            FROM journal_entries j
            JOIN journal_entry_lines l ON j.journal_id = l.journal_id
            WHERE l.account_code != %s
            ORDER BY year, month
            """, (retained_code,))
            rows = cursor.fetchall()
            if not rows:
                return []
            # Find the earliest year
            earliest_year = rows[0][0]

            # Get all months from the earliest year
            months_in_year = [month for year, month in rows if year == earliest_year]
            if not months_in_year:
                return []
            first_month = min(months_in_year)
            last_month = max(months_in_year)
            first_month_name = calendar.month_name[first_month]
            last_month_name = calendar.month_name[last_month]
            formatted_period =f"{first_month_name} {earliest_year} - {last_month_name} {earliest_year}"
            return [formatted_period]
    except Exception as e:
        return f"Error fetching periods: {str(e)}"

def get_available_years_from_jornal_archive(conn):
    """
    Fetch distinct years from journal_archive (period_end_year)
    Returns list like ["2023", 2024]
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT period_end_year
                FROM journal_archive
                ORDER BY period_end_year
            """)
            years = [str(row[0]) for row in cursor.fetchall()]
            return years
    except Exception as e:
        return f"Error fetching available years: {str(e)}"

