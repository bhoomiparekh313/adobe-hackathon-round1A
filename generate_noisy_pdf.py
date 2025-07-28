from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import random
import os

os.makedirs("input", exist_ok=True)
filename = "input/noisy_test_50pages.pdf"

styles = getSampleStyleSheet()
title_style = styles['Title']
h1_style = styles['Heading1']
h2_style = styles['Heading2']
h3_style = styles['Heading3']
normal_style = styles['BodyText']

def random_text(length=12):
    # Simple random word text with some noise characters
    words = ["Lorem", "ipsum", "dolor", "sit", "amet", "consectetur", 
             "adipiscing", "elit", "Phasellus", "imperdiet", "1234567890", 
             "email@example.com", "*", "-", "•", "(", ")", "[", "]"]
    return ' '.join(random.choice(words) for _ in range(length))

c = canvas.Canvas(filename, pagesize=letter)
width, height = letter

for page_num in range(1, 51):
    c.setFont("Helvetica-Bold", 18)
    c.drawString(inch, height - inch, f"Document Title - Page {page_num}")
    
    # Add a noisy header line (junk chars + small)
    c.setFont("Helvetica", 9)
    noisy_line = random.choice(["* * * * *", "!!! ### $$$", "--- ...", "??? !!!"] + [random_text(5)])
    c.drawString(inch, height - inch - 20, noisy_line)
    
    y = height - inch - 60
    for section_num in range(1, 12):
        # Pick heading level randomly with font size and style
        level = random.choices(['H1', 'H2', 'H3'], weights=[0.25,0.45,0.30])[0]
        if level == 'H1':
            c.setFont("Helvetica-Bold", 14)
        elif level == 'H2':
            c.setFont("Helvetica-BoldOblique", 12)
        else:
            c.setFont("Helvetica-Oblique", 10)
        
        # Draw heading text with some repeated noise possibly
        heading_text = f"{level} Heading {section_num} - " + random_text(4)
        if random.random() < 0.15:
            heading_text += " *"
        c.drawString(inch + (section_num % 3) * 20, y, heading_text)
        y -= 18
        
        # Add some noise paragraphs and bullet lists below heading
        c.setFont("Helvetica", 9)
        for _ in range(random.randint(2,4)):
            text_line = random_text(random.randint(5,10))
            if random.random() < 0.3:
                # Add bullet points and emails sometimes
                bullet = random.choice(["•", "-"])
                if random.random() < 0.5:
                    text_line = bullet + " " + text_line
                else:
                    text_line = text_line + " email@example.com"
            c.drawString(inch + 15, y, text_line)
            y -= 12
            
            # Simulate line breaks in text to create soft wraps
            if random.random() < 0.2 and y > inch:
                wrapped_text = random_text(random.randint(3,7))
                c.drawString(inch + 30, y, wrapped_text)
                y -= 12
        
        # Random gap before next section
        y -= random.randint(5, 15)
        if y < inch:
            break
    
    c.showPage()

c.save()

print(f"Generated {filename} successfully with noise and multi-level structure.")
