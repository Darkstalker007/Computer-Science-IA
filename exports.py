from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

def generate_student_attendance_pdf(student_name, student_id, attendance_records):
    filename = f"attendance_history_{student_id}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    title = Paragraph(f"Attendance History - {student_name}", styles['Heading1'])
    elements.append(title)
    
    table_data = [['Date', 'Class', 'Status']]
    for record in attendance_records:
        table_data.append([
            record.date.strftime('%Y-%m-%d'),
            record.class_.name,
            record.status
        ])
    
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    doc.build(elements)
    return filename

def generate_class_attendance_pdf(class_name, class_id, attendance_records):
    from models import User  # Import the User model at the beginning of the function
    
    filename = f"class_attendance_{class_id}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    title = Paragraph(f"Class Attendance Report - {class_name}", styles['Heading1'])
    elements.append(title)
    
    table_data = [['Student Name', 'Date', 'Status']]
    for record in attendance_records:
        student = User.query.get(record.student_id)
        table_data.append([
            student.name,
            record.date.strftime('%Y-%m-%d'),
            record.status
        ])
    
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    doc.build(elements)
    return filename
