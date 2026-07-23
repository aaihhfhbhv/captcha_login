import cv2

def preprocess_captcha(img_path):
    img = cv2.imread(img_path)
    if img is None:
        raise FileNotFoundError(f"无法读取图片 {img_path}")
    img_denoise = cv2.fastNlMeansDenoisingColored(img, None, h=6, hColor=6, templateWindowSize=7, searchWindowSize=21)
    gaussian = cv2.GaussianBlur(img_denoise, (0, 0), sigmaX=1.2)
    img_sharp = cv2.addWeighted(img_denoise, 1.5, gaussian, -0.5, 0)
    output_processed = f"{img_path}_proc.jpg"
    cv2.imwrite(output_processed, img_sharp)
    return output_processed