# 二进制文件说明

由于Python环境限制，以下二进制格式文件需要手动创建或使用专门工具生成：

## PDF文件
推荐使用以下Python库生成：
- reportlab: 创建复杂PDF报告
- fpdf2: 轻量级PDF生成
- weasyprint: HTML转PDF

示例命令：
```bash
pip install reportlab
python -c "
from reportlab.pdfgen import canvas
c = canvas.Canvas('test_data/sample_report.pdf')
c.drawString(100, 750, 'MCP测试框架报告')
c.drawString(100, 730, '这是一个测试PDF文件')
c.save()
"
```

## Word文档 (.docx)
推荐使用python-docx库：
```bash
pip install python-docx
python -c "
from docx import Document
doc = Document()
doc.add_heading('MCP测试文档', 0)
doc.add_paragraph('这是一个测试Word文档，包含了MCP工具的相关信息。')
doc.save('test_data/sample_document.docx')
"
```

## PowerPoint演示文稿 (.pptx)
推荐使用python-pptx库：
```bash
pip install python-pptx
python -c "
from pptx import Presentation
prs = Presentation()
title_slide = prs.slides.add_slide(prs.slide_layouts[0])
title_slide.shapes.title.text = 'MCP测试框架'
title_slide.shapes.placeholders[1].text = '自动化MCP工具测试解决方案'
prs.save('test_data/sample_presentation.pptx')
"
```

## 图片文件
可以使用PIL生成测试图片：
```bash
pip install Pillow
python -c "
from PIL import Image, ImageDraw, ImageFont
img = Image.new('RGB', (800, 600), color='white')
draw = ImageDraw.Draw(img)
draw.text((50, 50), 'MCP Test Image', fill='black')
img.save('test_data/sample_image.png')
"
```
