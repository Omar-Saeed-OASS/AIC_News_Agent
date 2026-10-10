import os
from pathlib import Path
import logging
import google.auth
from google.auth.exceptions import GoogleAuthError
from google.oauth2.service_account import Credentials
import gspread
from gspread.exceptions import GSpreadException, APIError
from dotenv import load_dotenv
load_dotenv()

# Configure the Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

CURRENT_DIR = Path(__file__).resolve().parent
KEY_PATH = CURRENT_DIR / "news_service_account.json"

def get_email_from_sheet(spreadsheet_id, email_sheet_id):
    """Reads the sheet, finds the active PIC, and compiles the unique CC list"""
    if not spreadsheet_id or not email_sheet_id:
        logger.error("SPREADSHEET_ID or EMAILSHEET_ID is missing from environment variables.")
        return None, []

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly"
    ]

    try:
        # Local Fallback: If local JSON key exists, use it
        if KEY_PATH.exists():
            logger.info("Local key found. Authenticating via service account JSON...")
            credentials = Credentials.from_service_account_file(str(KEY_PATH), scopes=scopes)

        # Cloud Run Native: Pull credentials automatically from Cloud Run metadata
        else:
            logger.info("Authenticating via Google Cloud Application Default Credentials...")
            credentials, _ = google.auth.default(scopes=scopes)

        gc = gspread.authorize(credentials)
        sheet = gc.open_by_key(spreadsheet_id).worksheet(email_sheet_id)
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


