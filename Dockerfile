# ============================
# 1️⃣ Base image
# ============================
FROM python:3.11-slim

# ============================
# 2️⃣ Set working directory
# ============================
WORKDIR /app

# ============================
# 3️⃣ Copy requirements
# ============================
COPY requirements.txt .

# Atualiza pip e instala dependências
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# ============================
# 4️⃣ Copy application files
# ============================
COPY . .

# ============================
# 5️⃣ Expose Flask port
# ============================
EXPOSE 5000

# ============================
# 6️⃣ Start the app with Gunicorn
# ============================
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
