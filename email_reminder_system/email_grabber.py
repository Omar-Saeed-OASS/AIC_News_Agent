import os
import logging
import google.auth
from google.auth.exceptions import GoogleAuthError
import gspread
from gspread.exceptions import GSpreadException, APIError
from dotenv import load_dotenv

# Configure the Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

load_dotenv()
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")
EMAILS_SHEET = os.environ.get("EMAILS_SHEET")


def get_email_from_sheet(sheet_id):
    """Reads the sheet, finds the active PIC, and compiles the unique CC list"""
    if not sheet_id:
        logger.error("SPREADSHEET_ID is missing from environment variables.")
        return None, []

    # Try-Except Block for Network & API Calls
    try:
        logger.info("Authenticating with Google Cloud...")
        scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        credentials, _ = google.auth.default(scopes=scopes)
        gc = gspread.authorize(credentials)

        logger.info("Opening spreadsheet and fetching 'emails' worksheet...")
        sheet = gc.open_by_key(sheet_id).worksheet(EMAILS_SHEET)
        records = sheet.get_all_records()

    except GoogleAuthError as e:
        logger.error(f"Google Authentication failed: {e}")
        return None, []
    except (GSpreadException, APIError) as e:
        logger.error(f"Google Sheets API error: {e}")
        return None, []
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return None, []

    logger.info(f"Successfully fetched {len(records)} records. Parsing routing...")

    unique_team = {}
    pic = None

    for row in records:
        name = str(row.get("Name", "")).strip()
        email = str(row.get("Email", "")).strip()
        status = str(row.get("Status", "")).strip()
        date_str = str(row.get("Date", "")).strip()

        # Register every unique member we find to build the CC list
        if email and email not in unique_team:
            unique_team[email] = {"name": name, "email": email}

        # The first row marked "Not Done" is the current PIC
        if status == "Not Done" and pic is None:
            pic = {"name": name, "email": email, "date": date_str}

    # Create the CC list by including everyone except the current PIC
    if pic:
        cc_list = [
            member for mail, member in unique_team.items()
            if mail != pic["email"]
        ]
    else:
        cc_list = list(unique_team.values())

    logger.info("Routing parsed successfully.")
    return pic, cc_list
