selenium_bilibili.py内替换你的B站账号与密码，运行main.py

常见问题：onnxruntime DLL 加载失败，是 Windows 环境缺少 VC++ 运行库
解决：
  1、
  pip uninstall onnxruntime onnxruntime-gpu -y
  pip install onnxruntime==1.15.1
  2、
  https://learn.microsoft.com/zh-CN/cpp/windows/latest-supported-vc-redist?view=msvc-170
  下载 vc_redist.x64.exe 安装，重启电脑后再运行脚本。

此外，ddddocr识别效果可能不佳，建议在captcha_preprocess.py上对图片灰度处理、局部二值化（关键是削弱背景轮廓）。