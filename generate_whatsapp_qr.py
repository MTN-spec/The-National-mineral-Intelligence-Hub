"""
Generate High-Resolution Presentation-Ready WhatsApp QR Codes
For Takunda Nigel Mhandu — The National Mineral Intelligence Hub
"""

import os
import qrcode
import qrcode.image.svg
from PIL import Image, ImageDraw, ImageFont

def generate_qr():
    whatsapp_url = "https://wa.me/263779770395?text=Hello%20Takunda%2C%20I%20am%20contacting%20you%20regarding%20The%20National%20Mineral%20Intelligence%20Hub"
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # -------------------------------------------------------------
    # 1. STANDALONE HIGH-RES QR CODE (PNG)
    # -------------------------------------------------------------
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction to allow center icon
        box_size=20,
        border=3,
    )
    qr.add_data(whatsapp_url)
    qr.make(fit=True)

    # WhatsApp Brand Colors
    # Primary green: #25D366, Dark green: #128C7E, Deep background: #075E54
    qr_img = qr.make_image(fill_color="#0b1b24", back_color="#ffffff").convert("RGBA")
    
    # Add a WhatsApp-style circular badge in the center
    qr_w, qr_h = qr_img.size
    badge_size = int(qr_w * 0.22)
    badge = Image.new("RGBA", (badge_size, badge_size), (0, 0, 0, 0))
    badge_draw = ImageDraw.Draw(badge)
    
    # White background circle with subtle shadow/border
    badge_draw.ellipse([(0, 0), (badge_size - 1, badge_size - 1)], fill="#ffffff", outline="#25D366", width=4)
    # Inner green circle
    inner_pad = int(badge_size * 0.08)
    badge_draw.ellipse([(inner_pad, inner_pad), (badge_size - inner_pad - 1, badge_size - inner_pad - 1)], fill="#25D366")
    
    # Draw simple phone receiver icon in white inside badge
    # Draw phone handset shape
    cx, cy = badge_size // 2, badge_size // 2
    r = badge_size // 4
    # Simple clean phone icon representation
    badge_draw.arc([(cx - r, cy - r), (cx + r, cy + r)], start=120, end=300, fill="#ffffff", width=int(badge_size * 0.09))
    badge_draw.ellipse([(cx - r - 2, cy - 2), (cx - r + 8, cy + 8)], fill="#ffffff")
    badge_draw.ellipse([(cx + 2, cy - r - 2), (cx + 12, cy - r + 8)], fill="#ffffff")
    
    badge_pos = ((qr_w - badge_size) // 2, (qr_h - badge_size) // 2)
    qr_img.paste(badge, badge_pos, mask=badge)
    
    out_qr_path = os.path.join(base_dir, "whatsapp_qr_takunda_mhandu.png")
    qr_img.save(out_qr_path, "PNG", dpi=(300, 300))
    print(f"[+] Saved High-Res QR: {out_qr_path}")

    # Copy to dashboard folder as well
    dash_qr_path = os.path.join(base_dir, "src", "dashboard", "whatsapp_qr_takunda_mhandu.png")
    qr_img.save(dash_qr_path, "PNG", dpi=(300, 300))

    # -------------------------------------------------------------
    # 2. VECTOR SVG QR CODE
    # -------------------------------------------------------------
    try:
        factory = qrcode.image.svg.SvgPathImage
        svg_qr = qrcode.make(whatsapp_url, image_factory=factory, error_correction=qrcode.constants.ERROR_CORRECT_H)
        svg_path = os.path.join(base_dir, "whatsapp_qr_code.svg")
        svg_qr.save(svg_path)
        print(f"[+] Saved Vector SVG QR: {svg_path}")
    except Exception as e:
        print(f"[-] SVG note: {e}")

    # -------------------------------------------------------------
    # 3. FULL HD PRESENTATION SLIDE (1920 x 1080)
    # -------------------------------------------------------------
    slide_w, slide_h = 1920, 1080
    slide = Image.new("RGBA", (slide_w, slide_h), "#060e15")
    draw = ImageDraw.Draw(slide)

    # Background ambient lighting / glow gradients
    # Top-right emerald ambient
    for i in range(160, 0, -5):
        alpha = int((160 - i) * 0.35)
        draw.ellipse([(slide_w - 700 - i*3, -200 - i*2), (slide_w + 300 + i*3, 600 + i*2)], fill=(37, 211, 102, alpha))
    
    # Bottom-left dark teal ambient
    for i in range(140, 0, -5):
        alpha = int((140 - i) * 0.25)
        draw.ellipse([(-200 - i*3, slide_h - 600 - i*2), (700 + i*3, slide_h + 300 + i*2)], fill=(6, 182, 212, alpha))

    # Load system fonts with fallback
    def get_font(size, bold=False):
        font_names = [
            "C:\\Windows\\Fonts\\segoeui.ttf",
            "C:\\Windows\\Fonts\\arial.ttf",
            "C:\\Windows\\Fonts\\calibri.ttf"
        ]
        if bold:
            font_names = [
                "C:\\Windows\\Fonts\\segoeuib.ttf",
                "C:\\Windows\\Fonts\\arialbd.ttf",
                "C:\\Windows\\Fonts\\calibrib.ttf"
            ]
        for fn in font_names:
            if os.path.exists(fn):
                try:
                    return ImageFont.truetype(fn, size)
                except Exception:
                    continue
        return ImageFont.load_default()

    font_title = get_font(52, bold=True)
    font_subtitle = get_font(26, bold=False)
    font_name = get_font(42, bold=True)
    font_role = get_font(24, bold=False)
    font_body = get_font(22, bold=False)
    font_body_bold = get_font(22, bold=True)
    font_scan_lbl = get_font(28, bold=True)

    # Top Header Pill / Badge
    pill_x, pill_y = 120, 90
    pill_w, pill_h = 490, 46
    draw.rounded_rectangle([(pill_x, pill_y), (pill_x + pill_w, pill_y + pill_h)], radius=23, fill="#0a2530", outline="#25D366", width=2)
    draw.text((pill_x + 28, pill_y + 10), "ZIMBABWE MINERAL INTELLIGENCE HUB", font=get_font(18, bold=True), fill="#25D366")

    # Main Slide Title
    draw.text((120, 160), "Let's Connect & Collaborate", font=font_title, fill="#ffffff")
    draw.text((120, 230), "Direct WhatsApp Advisory, Ground-Truth Validation & Strategic Partnerships", font=font_subtitle, fill="#94a3b8")

    # Left Column: Profile Card Container
    card_x, card_y = 120, 310
    card_w, card_h = 800, 640
    draw.rounded_rectangle([(card_x, card_y), (card_x + card_w, card_y + card_h)], radius=24, fill="#0b1722", outline="#1e293b", width=2)

    # Load and place user avatar if available
    avatar_path = os.path.join(base_dir, "user_profile.jpg")
    avatar_size = 140
    if os.path.exists(avatar_path):
        try:
            av = Image.open(avatar_path).convert("RGBA")
            av = av.resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)
            
            # Create circular mask
            mask = Image.new("L", (avatar_size, avatar_size), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse([(0, 0), (avatar_size, avatar_size)], fill=255)
            
            # Border ring around avatar
            draw.ellipse([(card_x + 46, card_y + 46), (card_x + 54 + avatar_size, card_y + 54 + avatar_size)], fill="#25D366")
            slide.paste(av, (card_x + 50, card_y + 50), mask=mask)
        except Exception as e:
            print("Avatar load exception:", e)
    else:
        # Fallback circle with initials
        draw.ellipse([(card_x + 50, card_y + 50), (card_x + 50 + avatar_size, card_y + 50 + avatar_size)], fill="#25D366")
        draw.text((card_x + 85, card_y + 85), "TM", font=get_font(48, bold=True), fill="#ffffff")

    # Name and Title
    name_x = card_x + 220
    draw.text((name_x, card_y + 60), "Takunda Nigel Mhandu", font=font_name, fill="#ffffff")
    draw.text((name_x, card_y + 115), "Lead Innovator & Systems Architect", font=font_role, fill="#25D366")
    draw.text((name_x, card_y + 148), "National Earth Observation & Mineral Intelligence", font=get_font(19), fill="#94a3b8")

    # Divider Line
    draw.line([(card_x + 50, card_y + 220), (card_x + card_w - 50, card_y + 220)], fill="#1e293b", width=2)

    # Details rows
    rows = [
        ("WhatsApp / Call:", "+263 779 770 395"),
        ("Official Email:", "mhandutakunda@gmail.com"),
        ("Specialization:", "GIS, Remote Sensing & Spectral Ore Exploration"),
        ("Institution:", "National University of Science & Technology (NUST)"),
        ("Platform:", "The National Mineral Intelligence Hub (Zimbabwe 2026)")
    ]

    row_y = card_y + 250
    for label, val in rows:
        draw.text((card_x + 60, row_y), label, font=font_body, fill="#64748b")
        draw.text((card_x + 260, row_y), val, font=font_body_bold, fill="#f1f5f9")
        row_y += 62

    # Bottom Tag in Card
    draw.rounded_rectangle([(card_x + 50, card_y + card_h - 75), (card_x + card_w - 50, card_y + card_h - 25)], radius=12, fill="#06121c")
    draw.text((card_x + 75, card_y + card_h - 62), "Available for Mining Concession Inspections, GEE Remote Sensing & Keynotes", font=get_font(17), fill="#38bdf8")

    # Right Column: Big Scannable QR Code Card
    qr_card_x, qr_card_y = 1000, 310
    qr_card_w, qr_card_h = 800, 640
    draw.rounded_rectangle([(qr_card_x, qr_card_y), (qr_card_x + qr_card_w, qr_card_y + qr_card_h)], radius=24, fill="#0b1722", outline="#25D366", width=3)

    # Title over QR Code
    draw.text((qr_card_x + 200, qr_card_y + 35), "SCAN TO CHAT ON WHATSAPP", font=font_scan_lbl, fill="#25D366")

    # White Container for QR Code
    qr_box_size = 420
    qr_box_x = qr_card_x + (qr_card_w - qr_box_size) // 2
    qr_box_y = qr_card_y + 85
    draw.rounded_rectangle([(qr_box_x - 10, qr_box_y - 10), (qr_box_x + qr_box_size + 10, qr_box_y + qr_box_size + 10)], radius=20, fill="#ffffff")

    # Paste QR Code
    resized_qr = qr_img.resize((qr_box_size, qr_box_size), Image.Resampling.LANCZOS)
    slide.paste(resized_qr, (qr_box_x, qr_box_y), mask=resized_qr)

    # Scannable Link text under QR
    link_text = "https://wa.me/263779770395"
    draw.text((qr_card_x + 235, qr_card_y + 535), link_text, font=get_font(24, bold=True), fill="#ffffff")
    draw.text((qr_card_x + 185, qr_card_y + 575), "Point phone camera or WhatsApp scanner to start conversation", font=get_font(18), fill="#94a3b8")

    # Footer Watermark
    draw.text((120, slide_h - 55), "The National Mineral Intelligence Hub  •  Zimbabwe Sovereign Innovation  •  2026", font=get_font(16), fill="#475569")

    out_slide_path = os.path.join(base_dir, "whatsapp_presentation_slide.png")
    slide.convert("RGB").save(out_slide_path, "PNG", dpi=(300, 300))
    print(f"[+] Saved Presentation Slide: {out_slide_path}")

    # Copy to dashboard folder
    dash_slide_path = os.path.join(base_dir, "src", "dashboard", "whatsapp_presentation_slide.png")
    slide.convert("RGB").save(dash_slide_path, "PNG", dpi=(300, 300))

if __name__ == "__main__":
    generate_qr()
