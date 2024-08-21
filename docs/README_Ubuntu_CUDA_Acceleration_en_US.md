
# Ubuntu 22.04 LTS

### 1. Check if NVIDIA Drivers Are Installed
   ```sh
   nvidia-smi
   ```
   If you see information similar to the following, it means that the NVIDIA drivers are already installed, and you can skip Step 2.
   ```plaintext
   +---------------------------------------------------------------------------------------+
   | NVIDIA-SMI 537.34                 Driver Version: 537.34       CUDA Version: 12.2     |
   |-----------------------------------------+----------------------+----------------------+
   | GPU  Name                     TCC/WDDM  | Bus-Id        Disp.A | Volatile Uncorr. ECC |
   | Fan  Temp   Perf          Pwr:Usage/Cap |         Memory-Usage | GPU-Util  Compute M. |
   |                                         |                      |               MIG M. |
   |=========================================+======================+======================|
   |   0  NVIDIA GeForce RTX 3060 Ti   WDDM  | 00000000:01:00.0  On |                  N/A |
   |  0%   51C    P8              12W / 200W |   1489MiB /  8192MiB |      5%      Default |
   |                                         |                      |                  N/A |
   +-----------------------------------------+----------------------+----------------------+
   ```

### 2. Install the Driver
   If no driver is installed, use the following command:
   ```sh
   sudo apt-get update
   sudo apt-get install nvidia-driver-545
   ```
   Install the proprietary driver and restart your computer after installation.
   ```sh
   reboot
   ```

### 3. Install Anaconda
   If Anaconda is already installed, skip this step.
   ```sh
   wget https://repo.anaconda.com/archive/Anaconda3-2024.06-1-Linux-x86_64.sh
   bash Anaconda3-2024.06-1-Linux-x86_64.sh
   ```
   In the final step, enter `yes`, close the terminal, and reopen it.

### 4. Create an Environment Using Conda
   Specify Python version 3.10.
   ```sh
   conda create -n MinerU python=3.10
   conda activate MinerU
   ```

### 5. Install Applications
   ```sh
   pip install magic-pdf[full]==0.7.0b1 --extra-index-url https://wheels.myhloli.com
   ```
❗ After installation, make sure to check the version of `magic-pdf` using the following command:
   ```sh
   magic-pdf --version
   ```
   If the version number is less than 0.7.0, please report the issue.

### 6. Download Models
   Refer to detailed instructions on [how to download model files](how_to_download_models_en.md).  
   After downloading, move the `models` directory to an SSD with more space.
   
❗ After downloading the models, ensure they are complete:
   - Check that the file sizes match the description on the website.
   - If possible, verify the integrity using SHA256.

### 7. Configuration Before First Run
   Obtain the configuration template file `magic-pdf.template.json` from the root directory of the repository.
   
❗ Execute the following command to copy the configuration file to your home directory, otherwise the program will not run:
   ```sh
   wget https://github.com/opendatalab/MinerU/raw/master/magic-pdf.template.json
   cp magic-pdf.template.json ~/magic-pdf.json
   ```
   Find the `magic-pdf.json` file in your home directory and configure `"models-dir"` to be the directory where the model weights from Step 6 were downloaded.
   
❗ Correctly specify the absolute path of the directory containing the model weights; otherwise, the program will fail due to missing model files.
   ```json
   {
     "models-dir": "/tmp/models"
   }
   ```

### 8. First Run
   Download a sample file from the repository and test it.
   ```sh
   wget https://github.com/opendatalab/MinerU/raw/master/demo/small_ocr.pdf
   magic-pdf -p small_ocr.pdf
   ```

### 9. Test CUDA Acceleration

If your graphics card has at least 8GB of VRAM, follow these steps to test CUDA acceleration:

1. Modify the value of `"device-mode"` in the `magic-pdf.json` configuration file located in your home directory.
   ```json
   {
     "device-mode": "cuda"
   }
   ```
2. Test CUDA acceleration with the following command:
   ```sh
   magic-pdf -p small_ocr.pdf
   ```

### 10. Enable CUDA Acceleration for OCR

❗ The following operations require a graphics card with at least 16GB of VRAM; otherwise, the program may crash or experience reduced performance.
    
1. Download `paddlepaddle-gpu`. Installation will automatically enable OCR acceleration.
   ```sh
   python -m pip install paddlepaddle-gpu==3.0.0b1 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/
   ```
2. Test OCR acceleration with the following command:
   ```sh
   magic-pdf -p small_ocr.pdf
   ```
