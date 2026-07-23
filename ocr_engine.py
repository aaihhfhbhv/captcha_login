import cv2
import ddddocr
from captcha_preprocess import preprocess_captcha

# ddddocr全局初始化（只初始化一次）
ocr_det = ddddocr.DdddOcr(det=True, show_ad=False)
ocr_cls = ddddocr.DdddOcr(det=False, show_ad=False)

# 计算包围盒IOU，用于文字框去重
def box_iou(box1, box2):
    x1_1, y1_1, x2_1, y2_1 = box1
    x1_2, y1_2, x2_2, y2_2 = box2
    inter_x1 = max(x1_1, x1_2)
    inter_y1 = max(y1_1, y1_2)
    inter_x2 = min(x2_1, x2_2)
    inter_y2 = min(y2_1, y2_2)
    if inter_x1 >= inter_x2 or inter_y1 >= inter_y2:
        return 0.0
    inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
    area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
    area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
    union_area = area1 + area2 - inter_area
    return inter_area / union_area

def mox(dummy_reader, image_path):
    proc_path = preprocess_captcha(image_path)
    img = cv2.imread(proc_path)
    with open(proc_path, "rb") as f:
        img_bytes = f.read()
    bbox_list = ocr_det.detection(img_bytes)
    # 重叠框去重
    unique_boxes = []
    for curr_box in bbox_list:
        duplicate = False
        for exist_box in unique_boxes:
            iou_val = box_iou(curr_box, exist_box)
            if iou_val > 0.5:
                duplicate = True
                break
        if not duplicate:
            unique_boxes.append(curr_box)
    # 单字裁剪识别
    result = []
    for bbox in unique_boxes:
        x1, y1, x2, y2 = bbox
        crop_img = img[y1:y2, x1:x2]
        _, crop_buf = cv2.imencode(".jpg", crop_img)
        crop_bytes = crop_buf.tobytes()
        text = ocr_cls.classification(crop_bytes)
        four_point = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
        result.append([four_point, text, 0.9])
    return result