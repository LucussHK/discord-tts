# Discord TTS 語音轉換工具

[Click to checkout the English version](README.md)

這款桌面應用能將文字即時轉換為語音，透過虛擬音訊裝置傳送至 Discord 語音頻道。  
無論是麥克風故障、不方便開口說話，或是單純偏好文字輸入的使用者，都能輕鬆參與語音對話。

本工具雖為 Discord 設計，但也可應用於**任何支援語音輸入的軟體**，展現高度彈性的音訊路由能力。

<img src="https://github.com/user-attachments/assets/351b3f2d-7918-4f60-9d4c-0e428e8cd50f" alt="Discord TTS App" width="550"/>

## 主要功能

- **Edge 語音引擎**：採用 Microsoft Edge TTS 技術，生成自然流暢的語音
- **多國語言支援**：預設支援英/中（簡體/繁體/香港），可自行擴充其他語系
- **聲音風格選擇**：每種語言提供多種發聲角色
- **語速控制**：自由調整語音播放速率
- **歷史紀錄**：完整保存已傳送的語音訊息
- **預聽功能**：傳送前預覽語音效果
- **現代化介面**：基於 CustomTkinter 打造的簡潔操作介面

## 技術原理

運用 Microsoft Edge 的 TTS 引擎將文字轉為音訊，透過虛擬音訊裝置模擬麥克風輸入，讓 Discord 誤判為真實語音輸入。

## 系統需求

- Windows 10 / 11
- Python 3.7 以上版本
- VB-Cable 虛擬音訊裝置（安裝包已內含）
- FFmpeg（音訊處理核心）

## 安裝教學

### 方案一：直接安裝版本（Windows 推薦）

1. 至 [Releases](https://github.com/LucussHK/discord-tts/releases) 下載最新安裝檔  
2. 執行安裝程式，將自動完成：
   - 主程式安裝  
   - VB-Cable 虛擬音訊驅動安裝  
   - 建立開始功能表捷徑  

### 方案二：原始碼編譯安裝

1. 複製專案倉庫：
   ```bash
   git clone https://github.com/LucussHK/discord-tts.git
   cd discord-tts
   ```

2. 建立虛擬環境（建議）：
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. 安裝必要套件：
   ```bash
   pip install -r requirements.txt
   ```

4. 下載外部依賴：
   - **FFmpeg**：從 [官方網站](https://ffmpeg.org/download.html) 或 [第三方編譯版](https://www.gyan.dev/ffmpeg/builds/) 取得，將 `ffmpeg.exe` 與 `ffprobe.exe` 置於專案根目錄  
   - **VB-Cable**：前往 [VB-Audio 官網](https://vb-audio.com/Cable/) 安裝驅動程式

5. 啟動應用程式：
   ```bash
   python discord_tts_app.py
   ```

## Discord 設定指南

1. 開啟 Discord 並加入語音頻道  
2. 進入「使用者設定」→「語音與視訊」  
3. 設定輸入裝置為「CABLE Output (VB-Audio Virtual Cable)」  
4. 確保使用「語音感應」模式（非按鍵發話）  

## 操作教學

1. 啟動 Discord TTS 工具  
2. 配置音訊路由：
   - Discord 輸出端：選擇 CABLE Input（VB-Audio Virtual Cable）  
   - 監聽裝置：設定為您的耳機或喇叭  
3. 選擇語言與發聲角色  
4. 在輸入框輸入文字內容  
5. 點擊「Speak in Discord」或按下 Enter 鍵，即可將語音傳至 Discord

## 🎙️ 音訊路由注意事項

為確保音訊正常傳輸：

- 在 **Discord → 語音與視訊設定** 中，輸入裝置應設定為：

  ![Discord Input Device](https://github.com/user-attachments/assets/80917fcb-4de3-49ac-a27a-986091a6670b)  
  *(預設值：CABLE Output (VB-Audio Virtual Cable))*

> ⚠️ **重要提醒**：請**保持** Discord 的「輸出裝置」為原有設定，僅需調整輸入裝置  
> 輸出裝置應維持您慣用的播放設備，才能正常收聽其他使用者語音

💡 進階應用：本工具亦可搭配 **Zoom / Skype / VRChat** 等語音軟體使用，只需將這些軟體的麥克風設定為 VB-Cable 即可

## 專案架構

主要程式檔案說明：
- `discord_tts_app.py`：應用程式主體  
- `subprocess_wrapper.py`：隱藏命令提示字元的輔助模組  
- `requirements.txt`：Python 依賴套件清單  
- `icon.ico`：應用程式圖示  

需手動下載的檔案（因體積過大未包含）：
- `ffmpeg.exe`：音訊處理核心元件  
- `ffprobe.exe`：音訊分析工具  

## 執行檔打包教學

使用 PyInstaller 生成單一執行檔：

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=icon.ico --name discord_tts_app --add-binary "ffmpeg.exe;." --add-binary "ffprobe.exe;." --add-data "subprocess_wrapper.py;." --add-data "icon.ico;." discord_tts_app.py
```

## 常見問題排除

- **Discord 無聲問題**：確認 VB-Cable 安裝正確，檢查應用程式與 Discord 的輸入裝置是否匹配  
- **FFmpeg 缺失錯誤**：確保 `ffmpeg.exe` 與 `ffprobe.exe` 位於程式根目錄  
- **語音延遲卡頓**：嘗試調整設定中的緩衝區大小參數  
- **程式閃退現象**：檢查是否安裝所有必要依賴套件  

## 授權條款

本專案採用 MIT 授權條款，詳見 LICENSE 檔案。

## 致謝名單

- [Microsoft Edge TTS](https://github.com/rany2/edge-tts)：語音合成引擎核心  
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)：現代化介面框架  
- [VB-Audio](https://vb-audio.com)：虛擬音訊裝置解決方案  
- [FFmpeg](https://ffmpeg.org/)：音訊處理基礎架構  
