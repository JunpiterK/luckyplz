# FPDF 기본 인코딩 문제 해결을 위해 utf-8 지원되는 ReportLab으로 대체
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# PDF 저장 경로
file_path = "/mnt/data/AI_Ethics_QA.pdf"

# PDF 생성
c = canvas.Canvas(file_path, pagesize=A4)
width, height = A4

# 기본 설정
c.setFont("Helvetica-Bold", 16)
c.drawCentredString(width / 2, height - 50, "AI 윤리 및 초지능 관련 Q&A 정리")

c.setFont("Helvetica", 11)
y_position = height - 80

for qa in qa_pairs:
    question = qa["question"]
    answer = qa["answer"]

    c.setFont("Helvetica-Bold", 12)
    for line in question.split('\n'):
        c.drawString(50, y_position, line)
        y_position -= 18

    c.setFont("Helvetica", 11)
    for line in answer.split('\n'):
        # 자동 줄바꿈 처리
        while len(line) > 100:
            c.drawString(60, y_position, line[:100])
            line = line[100:]
            y_position -= 14
        c.drawString(60, y_position, line)
        y_position -= 18

    y_position -= 10
    if y_position < 100:
        c.showPage()
        y_position = height - 50
        c.setFont("Helvetica", 11)

# 저장
c.save()

file_path