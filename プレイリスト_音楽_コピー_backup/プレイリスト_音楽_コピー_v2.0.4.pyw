# version: 2.0.0
# -*- coding: utf-8 -*-

import os
import shutil
import tkinter as tk
import threading
import json
import urllib.request
import urllib.error
import webbrowser
from tkinter import ttk, filedialog, messagebox, scrolledtext

# --- コンソールウィンドウを非表示にする (Windows用) ---
try:
    import ctypes
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd != 0:
        ctypes.windll.user32.ShowWindow(hwnd, 0)
except Exception:
    pass

# --- 高DPI対応 (Windows向け) ---
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# =============================================================================
# 定数定義
# =============================================================================
APP_VERSION = "2.0.4"
APP_TITLE = f"プレイリスト音楽ファイルコピー v{APP_VERSION}"

# GitHubリポジトリ情報
GITHUB_USER = "kazu-1234" 
GITHUB_REPO = "Playlist_Music_Copy"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"

# =============================================================================
# アプリケーションクラス
# =============================================================================
class PlaylistCopierApp(tk.Tk):
    """
    プレイリスト音楽ファイルコピー用のGUIアプリケーション
    v2.0.4:
      - ウィンドウサイズ固定とUI表示調整
    v2.0.3:
      - ログ枠の高さ固定とウィンドウサイズの最適化
    v2.0.2:
      - ログエリアをさらに縮小
      - テキストの視認性向上
    v2.0.1:
      - ログエリアを縮小
      - GitHubアップデート確認機能を追加
    v2.0.0:
      - UIをモダンなタブ形式に変更 (iPhone_Photo_Renamer準拠)
      - マルチスレッド処理によるUIの応答性向上
    """
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("650x520")
        self.resizable(False, False)
        # self.minsize(600, 400) # サイズ固定のため不要だが残しても害はない
        
        # --- 変数定義 ---
        self.playlist_path = tk.StringVar()
        self.destination_folder = tk.StringVar()
        self.is_processing = False
        
        self.progress_label_var = tk.StringVar()
        
        # --- UIセットアップ ---
        self._setup_ui()

    def _setup_ui(self):
        """タブUIの構築"""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ノートブック（タブ）の作成
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 1. メインタブ
        self.main_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.main_tab, text="メイン")
        self._setup_main_tab_content()

        # 2. 設定タブ
        self.settings_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.settings_tab, text="設定")
        self._setup_settings_tab_content()

    def _setup_main_tab_content(self):
        """メイン機能のUI構築"""
        parent = self.main_tab

        # 1. プレイリスト選択フレーム
        playlist_frame = ttk.LabelFrame(parent, text="ステップ1: プレイリストの選択", padding="10")
        playlist_frame.pack(fill=tk.X, pady=5)
        
        entry_frame = ttk.Frame(playlist_frame)
        entry_frame.pack(fill=tk.X, pady=5)
        
        ttk.Entry(entry_frame, textvariable=self.playlist_path, state='readonly').pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(entry_frame, text="ファイルを選択", command=self.select_playlist).pack(side=tk.LEFT)
        
        ttk.Label(playlist_frame, text="対応形式: .m3u, .m3u8 (UTF-8推奨)", foreground="#333333", font=("", 9)).pack(anchor=tk.W)

        # 2. 保存先設定フレーム
        dest_frame = ttk.LabelFrame(parent, text="ステップ2: 保存先フォルダの選択", padding="10")
        dest_frame.pack(fill=tk.X, pady=5)

        dest_entry_frame = ttk.Frame(dest_frame)
        dest_entry_frame.pack(fill=tk.X, pady=5)

        ttk.Entry(dest_entry_frame, textvariable=self.destination_folder, state='readonly').pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(dest_entry_frame, text="フォルダを選択", command=self.select_destination).pack(side=tk.LEFT)

        # 3. 実行ボタン
        self.copy_button = ttk.Button(parent, text="コピーを開始", command=self.start_process)
        self.copy_button.pack(fill=tk.X, pady=15)
        
        # 4. 進捗表示フレーム
        self.progress_label = ttk.Label(parent, textvariable=self.progress_label_var)
        self.progress_label.pack(anchor=tk.W)
        self.progressbar = ttk.Progressbar(parent, mode='determinate')
        self.progressbar.pack(fill=tk.X, pady=(0, 5))

        # 5. ログ表示フレーム
        log_frame = ttk.LabelFrame(parent, text="ログ", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=False)

        self.log_text = tk.Text(log_frame, height=5, state="disabled", wrap="word")
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _setup_settings_tab_content(self):
        """設定・情報タブのUI構築"""
        parent = self.settings_tab

        # --- アップデート情報 ---
        update_frame = ttk.LabelFrame(parent, text="アップデート情報", padding="15")
        update_frame.pack(fill=tk.X, pady=10)

        title_font = ("Meiryo UI", 12, "bold")
        ttk.Label(update_frame, text="現在のバージョン", font=("Meiryo UI", 10)).pack(anchor=tk.W)
        ttk.Label(update_frame, text=f"v{APP_VERSION}", font=title_font, foreground="#007ACC").pack(anchor=tk.W, pady=(0, 10))

        self.update_status_var = tk.StringVar(value="最新のアップデートを確認できます")
        ttk.Label(update_frame, textvariable=self.update_status_var).pack(pady=5)

        self.check_update_btn = ttk.Button(update_frame, text="アップデートを確認", command=self._check_for_updates)
        self.check_update_btn.pack(pady=10)

        self.update_progress = ttk.Progressbar(update_frame, mode="indeterminate", length=200)

        # 免責事項
        disclaimer_frame = ttk.LabelFrame(parent, text="免責事項", padding="15")
        disclaimer_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        disclaimer_text = (
            "本ソフトウェアの使用により生じたいかなる損害（データの消失、破損、"
            "PCの不具合など）についても、開発者は一切の責任を負いません。\n\n"
            "必ずデータのバックアップを取った上でご使用ください。\n"
        )
        
        text_widget = tk.Text(disclaimer_frame, height=8, wrap="word", padx=5, pady=5, bg="#F0F0F0", relief="flat")
        text_widget.insert("1.0", disclaimer_text)
        text_widget.config(state="disabled")
        text_widget.pack(fill=tk.BOTH, expand=True)

    # --- UI操作ヘルパー ---
    def safe_log(self, message):
        self.after(0, self._log, message)

    def _log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def safe_update_progress(self, current, total):
        self.after(0, self._update_progress, current, total)

    def _update_progress(self, current, total):
        self.progressbar['maximum'] = total
        self.progressbar['value'] = current
        percent = int((current / total) * 100) if total > 0 else 0
        self.progress_label_var.set(f"処理中... {percent}% ({current}/{total})")

    def safe_reset_progress(self):
        self.after(0, self._reset_progress)
    
    def _reset_progress(self):
        self.progressbar['value'] = 0
        self.progress_label_var.set("待機中")

    def safe_enable_button(self):
        self.after(0, lambda: self.copy_button.config(state="normal"))

    def safe_show_info(self, title, message):
        self.after(0, lambda: messagebox.showinfo(title, message))
        
    def safe_show_error(self, title, message):
        self.after(0, lambda: messagebox.showerror(title, message))

    # --- イベントハンドラ ---
    def select_playlist(self):
        if self.is_processing: return
        file_path = filedialog.askopenfilename(
            title="プレイリストを選択してください",
            filetypes=[("プレイリスト", "*.m3u *.m3u8"), ("テキストファイル", "*.txt"), ("すべてのファイル", "*.*")]
        )
        if file_path:
            self.playlist_path.set(file_path)
            self._log(f"プレイリストを選択: {file_path}")

    def select_destination(self):
        if self.is_processing: return
        folder_path = filedialog.askdirectory(title="保存先フォルダを選択してください")
        if folder_path:
            self.destination_folder.set(folder_path)
            self._log(f"保存先を選択: {folder_path}")

    def start_process(self):
        playlist = self.playlist_path.get()
        dest = self.destination_folder.get()

        if not playlist:
            messagebox.showwarning("エラー", "プレイリストファイルが選択されていません。")
            return
        if not dest:
            messagebox.showwarning("エラー", "保存先フォルダが選択されていません。")
            return
        
        if not messagebox.askyesno("確認", "ファイルのコピーを開始しますか？"):
            return

        self.copy_button.config(state="disabled")
        self.is_processing = True
        self.safe_reset_progress()
        
        thread = threading.Thread(
            target=self.run_copy_thread,
            args=(playlist, dest),
            daemon=True
        )
        thread.start()

    # --- メインロジック ---
    def run_copy_thread(self, playlist_path, dest_folder):
        self.safe_log("="*30)
        self.safe_log("処理を開始します...")

        # 1. フォルダ作成確認
        if not os.path.exists(dest_folder):
            try:
                os.makedirs(dest_folder)
                self.safe_log(f"フォルダを作成しました: {dest_folder}")
            except Exception as e:
                self.safe_log(f"エラー: フォルダ作成失敗 - {e}")
                self.safe_show_error("エラー", f"フォルダ作成失敗:\n{e}")
                self.safe_enable_button()
                self.is_processing = False
                return

        # 2. プレイリスト読み込み
        lines = []
        try:
            with open(playlist_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            # Shift-JISなどでの再試行ロジックを入れるか、エラーにするか。
            # 今回はutf-8前提だが、単純なFallbackを入れる
            try:
                with open(playlist_path, 'r', encoding='cp932') as f:
                    lines = f.readlines()
                self.safe_log("注意: UTF-8での読み込みに失敗したため、CP932(Shift-JIS)で読み込みました。")
            except Exception as e:
                self.safe_log(f"エラー: プレイリスト読み込み失敗 - {e}")
                self.safe_show_error("エラー", f"読み込み失敗:\n{e}")
                self.safe_enable_button()
                self.is_processing = False
                return
        except Exception as e:
            self.safe_log(f"エラー: プレイリスト読み込み失敗 - {e}")
            self.safe_show_error("エラー", f"読み込み失敗:\n{e}")
            self.safe_enable_button()
            self.is_processing = False
            return

        # 有効な行を抽出
        valid_lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]
        total_files = len(valid_lines)
        
        self.safe_log(f"処理対象: {total_files} ファイル")
        self.safe_update_progress(0, total_files)

        copied_count = 0
        skipped_count = 0

        # 3. コピー処理ループ
        for i, source_path in enumerate(valid_lines):
            # 相対パス対応: プレイリストからの相対パスの場合、絶対パスに変換
            if not os.path.isabs(source_path):
                playlist_dir = os.path.dirname(playlist_path)
                source_path = os.path.normpath(os.path.join(playlist_dir, source_path))

            if os.path.isfile(source_path):
                original_file_name = os.path.basename(source_path)
                destination_path = os.path.join(dest_folder, original_file_name)
                
                # 同名ファイル回避ロジック (機能変更なし)
                final_file_name = original_file_name
                counter = 1
                while os.path.exists(destination_path):
                    name, ext = os.path.splitext(original_file_name)
                    final_file_name = f"{name} ({counter}){ext}"
                    destination_path = os.path.join(dest_folder, final_file_name)
                    counter += 1

                try:
                    if final_file_name != original_file_name:
                        self.safe_log(f"リネームコピー: ...{original_file_name[:15]} -> {final_file_name}")
                    
                    shutil.copy2(source_path, destination_path)
                    copied_count += 1
                except Exception as e:
                    self.safe_log(f"[エラー] コピー失敗: {e}")
                    skipped_count += 1
            else:
                self.safe_log(f"[スキップ] ファイル不在: {source_path}")
                skipped_count += 1

            # 進捗更新
            self.safe_update_progress(i + 1, total_files)

        # 4. 完了処理
        self.safe_log("-" * 30)
        final_msg = f"完了: {copied_count} 個成功 / {skipped_count} 個スキップ"
        self.safe_log(final_msg)
        self.safe_show_info("完了", final_msg)
        
        self.safe_enable_button()
        self.is_processing = False

    # --- アップデート確認ロジック ---
    def _check_for_updates(self):
        self.check_update_btn.config(state="disabled")
        self.update_status_var.set("更新を確認中...")
        self.update_progress.pack(pady=5)
        self.update_progress.start()
        
        threading.Thread(target=self._update_check_worker, daemon=True).start()

    def _update_check_worker(self):
        try:
            req = urllib.request.Request(GITHUB_API_URL)
            req.add_header('User-Agent', 'PlaylistMusicCopy')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
            
            tag_name = data.get("tag_name", "").lstrip("v")
            html_url = data.get("html_url", "")

            if not tag_name:
                raise Exception("バージョン情報を取得できませんでした")

            self.after(0, lambda: self._process_update_result(tag_name, html_url))

        except urllib.error.HTTPError as e:
            msg = "リポジトリが見つからないか、アクセスできません" if e.code == 404 else f"HTTPエラー: {e.code}"
            self.after(0, lambda: self._update_ui_error(msg))
        except Exception as e:
            self.after(0, lambda: self._update_ui_error(str(e)))

    def _process_update_result(self, latest_version, url):
        self.update_progress.stop()
        self.update_progress.pack_forget()
        self.check_update_btn.config(state="normal")

        current_ver_tuple = self._parse_version(APP_VERSION)
        latest_ver_tuple = self._parse_version(latest_version)

        if latest_ver_tuple > current_ver_tuple:
            self.update_status_var.set(f"新しいバージョン v{latest_version} があります")
            if messagebox.askyesno("アップデート", f"新しいバージョン v{latest_version} が利用可能です。\nダウンロードページを開きますか？"):
                webbrowser.open(url)
        else:
            self.update_status_var.set(f"お使いのバージョン (v{APP_VERSION}) は最新です")
            messagebox.showinfo("アップデート", "最新バージョンです。")

    def _parse_version(self, v_str):
        try:
            return tuple(map(int, v_str.split(".")))
        except ValueError:
            return (0, 0, 0)

    def _update_ui_error(self, message):
        self.update_progress.stop()
        self.update_progress.pack_forget()
        self.check_update_btn.config(state="normal")
        self.update_status_var.set("確認エラー")
        messagebox.showerror("エラー", f"アップデート確認に失敗しました:\n{message}\n\nGitHubリポジトリが公開されているか確認してください。")

if __name__ == '__main__':
    app = PlaylistCopierApp()
    app.mainloop()
