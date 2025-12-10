import qrcode
import json
import os

# List of 5 transactions
transactions = [
    {
        "merchant_id": "TM-BORROWDALE-001", "merchant_name": "TM Pick n Pay",
        "amount": 20.00, "currency": "USD", "reference": "INV-GROCERY-01", "timestamp": "2025-12-10T10:00:00"
    },
    {
        "merchant_id": "ZUVA-SAMORA-002", "merchant_name": "Zuva Petroleum",
        "amount": 50.00, "currency": "USD", "reference": "INV-FUEL-02", "timestamp": "2025-12-10T11:15:00"
    },
    {
        "merchant_id": "CHICKEN-INN-AVON", "merchant_name": "Chicken Inn",
        "amount": 12.50, "currency": "USD", "reference": "INV-LUNCH-03", "timestamp": "2025-12-10T13:30:00"
    },
    {
        "merchant_id": "ZESA-PREPAID", "merchant_name": "ZESA Token",
        "amount": 100.00, "currency": "USD", "reference": "INV-POWER-04", "timestamp": "2025-12-10T09:00:00"
    },
    {
        "merchant_id": "NYARADZO-FUNERAL", "merchant_name": "Nyaradzo Policy",
        "amount": 15.00, "currency": "USD", "reference": "INV-INSURE-05", "timestamp": "2025-12-10T14:45:00"
    }
]

# Generate QRs
for idx, data in enumerate(transactions):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(json.dumps(data))
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    filename = f"qr_sample_{idx+1}.png"
    img.save(filename)
    print(f"Generated {filename} for {data['merchant_name']} (${data['amount']})")
