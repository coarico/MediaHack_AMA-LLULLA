# Pesos del modelo de deteccion de video

Este microservicio usa un modelo de clasificacion de imagenes real-vs-fake
descargado en tiempo de ejecucion desde Hugging Face Hub. No se versiona
ningun binario de pesos en este repo.

- Modelo por defecto: `dima806/deepfake_vs_real_image_detection` (ViT, licencia abierta)
- Cambiar de modelo: variable de entorno `VIDEO_ML_MODEL_ID`
- Dispositivo: `VIDEO_ML_DEVICE=cpu` (default) o el indice de GPU, p. ej. `0`
- Modo test/CI sin descargar nada: `VIDEO_ML_MOCK=1`

## Pre-cachear pesos (para build de Docker)

```
python -c "from transformers import pipeline; pipeline('image-classification', model='dima806/deepfake_vs_real_image_detection')"
```

Esto deja los pesos en `~/.cache/huggingface`. En el Dockerfile del servicio
conviene correr este comando en el build stage para que el contenedor no
descargue nada en el primer request.

## Deteccion facial (heuristicas OpenCV): YuNet

`face_detection_yunet_2023mar.onnx` (~227KB, incluido en este repo) es el
detector facial [YuNet](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet)
de OpenCV Zoo (licencia MIT). Se usa en vez de los Haar Cascades clasicos
porque en OpenCV 5.x el binding `cv2.CascadeClassifier` fue removido; YuNet
es ademas mas preciso y sigue siendo un modelo muy liviano.

Ruta configurable con `VIDEO_FACE_DETECTOR_PATH` (default: este archivo).
