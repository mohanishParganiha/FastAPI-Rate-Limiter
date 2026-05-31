# ==============================================================================
# STAGE 1: Build & Dependency Collection
# ==============================================================================
FROM python:3.11-slim AS builder

WORKDIR /app

#prevent python from writing .pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1

#prevent python from buffering stdout/stderr(essential for real-time logging)
ENV PYTHONUNBUFFERED=1

#install system dependencies needed for compiling packages (if any)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# install your dependencies into a local direcotry wheels cache
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt


#=================================================================================
#STAGE 2: Final Runtime Image
#=================================================================================
FROM python:3.11-slim as runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
#ensure the application fallbacks port defaults to 8000
ENV PORT=8000

#copy installed python packages from the builder stage
COPY --from=builder /root/.local /root/.local
#update system path so the app can find globally installed tools like uvicorn
ENV PATH=/root/.local/bin:$PATH

#copy your actuall application codebase into the container
COPY . .

#expose the internal network port
EXPOSE ${PORT}

#copy entrypoin.sh and make it executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

#run the FastAPI serer using uvicorn
ENTRYPOINT [ "/entrypoint.sh" ]