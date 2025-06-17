# Headset Tracking System

A simple desktop application for tracking headset check-in and check-out using a barcode scanner.

## Features

- Check out headsets to attendees
- Check in returned headsets
- View all checked out devices
- Simple and intuitive interface
- Local SQLite database storage
- Export to Excel functionality

## Requirements

- Python 3.7+
- Windows/macOS/Linux
- Barcode scanner (USB HID keyboard emulation)

## Installation

1. Clone or download this repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```
   python main.py
   ```

2. **Check Out a Headset**:
   - Scan the barcode
   - Enter the attendee's name
   - Click "Check Out"

3. **Check In a Headset**:
   - Scan the barcode
   - Click "Check In"

4. **View Status**:
   - The main table shows all devices and their status
   - Green rows indicate checked-in devices
   - Red rows indicate checked-out devices

## Data Storage

All data is stored in a local SQLite database file named `headset_tracking.db` in the application directory.

## Exporting Data

To export the data to Excel, use the "Export to Excel" button. This will create a timestamped Excel file in the `exports` directory.

## Troubleshooting

- If the barcode scanner isn't working, make sure it's in "keyboard emulation" mode
- Ensure the cursor is in the barcode field when scanning
- Check that the database file has write permissions

## License

This project is licensed under the MIT License.
