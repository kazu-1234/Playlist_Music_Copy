# -*- coding: utf-8 -*-
import os
import shutil
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk

class PlaylistCopierApp(tk.Tk):
    """
    プレイリスト音楽ファイルコピー用のGUIアプリケーションクラス
    """
    def __init__(self):
        super().__init__()
        
        # --- ウィンドウの基本設定 ---
        self.title("プレイリスト音楽ファイルコピー")
        self.geometry("700x500") # ウィンドウサイズ

        # --- 変数の初期化 ---
        self.playlist_path = tk.StringVar()
        self.destination_folder = tk.StringVar()

        # --- UIウィジェットの作成と配置 ---
        self.create_widgets()

    def create_widgets(self):
        """
        アプリケーションのUIウィジェットを作成し、ウィンドウに配置するメソッド
        """
        # 見た目をモダンにするためのスタイル設定
        style = ttk.Style(self)
        style.theme_use('clam') # 'clam', 'alt', 'default', 'classic' などから選択

        # --- メインフレーム ---
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- 1. プレイリスト選択セクション ---
        playlist_frame = ttk.LabelFrame(main_frame, text="ステップ1: プレイリストを選択", padding="10")
        playlist_frame.pack(fill=tk.X, pady=5)

        playlist_entry = ttk.Entry(playlist_frame, textvariable=self.playlist_path, width=70, state='readonly')
        playlist_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        playlist_button = ttk.Button(playlist_frame, text="ファイルを選択...", command=self.select_playlist)
        playlist_button.pack(side=tk.LEFT)

        # --- 2. コピー先フォルダ選択セクション ---
        dest_frame = ttk.LabelFrame(main_frame, text="ステップ2: コピー先のフォルダを選択", padding="10")
        dest_frame.pack(fill=tk.X, pady=5)

        dest_entry = ttk.Entry(dest_frame, textvariable=self.destination_folder, width=70, state='readonly')
        dest_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        dest_button = ttk.Button(dest_frame, text="フォルダを選択...", command=self.select_destination)
        dest_button.pack(side=tk.LEFT)

        # --- 3. 実行ボタン ---
        self.copy_button = ttk.Button(main_frame, text="コピーを開始", command=self.start_copy, state='disabled')
        self.copy_button.pack(pady=10, fill=tk.X)

        # --- 4. ログ表示エリア ---
        log_frame = ttk.LabelFrame(main_frame, text="処理ログ", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=15)
        self.log_area.pack(fill=tk.BOTH, expand=True)
        self.log_area.configure(state='disabled') # 初期状態では編集不可にする

    def select_playlist(self):
        """プレイリストファイル選択ダイアログを表示し、パスを変数に格納する"""
        path = filedialog.askopenfilename(
            title="コピー元のプレイリストファイルを選択してください",
            filetypes=[("プレイリストファイル", "*.m3u *.m3u8"), ("テキストファイル", "*.txt"), ("すべてのファイル", "*.*")]
        )
        if path:
            self.playlist_path.set(path)
            self.log(f"プレイリストを選択しました: {path}")
            self.check_paths()

    def select_destination(self):
        """コピー先フォルダ選択ダイアログを表示し、パスを変数に格納する"""
        path = filedialog.askdirectory(
            title="音楽ファイルのコピー先のフォルダを選択してください"
        )
        if path:
            self.destination_folder.set(path)
            self.log(f"コピー先フォルダを選択しました: {path}")
            self.check_paths()

    def check_paths(self):
        """プレイリストとコピー先の両方が選択されているか確認し、ボタンの状態を更新する"""
        if self.playlist_path.get() and self.destination_folder.get():
            self.copy_button.config(state='normal')
        else:
            self.copy_button.config(state='disabled')

    def log(self, message):
        """ログエリアにメッセージを追記する"""
        self.log_area.configure(state='normal') # 編集可能にする
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END) # 自動で一番下までスクロール
        self.log_area.configure(state='disabled') # 再び編集不可にする
        self.update_idletasks() # UIを即時更新

    def start_copy(self):
        """コピー処理を開始する"""
        playlist = self.playlist_path.get()
        destination = self.destination_folder.get()

        if not messagebox.askokcancel("確認", "ファイルのコピーを開始しますか？"):
            return

        self.copy_button.config(state='disabled') # 処理中にボタンを無効化
        self.log("\n--- ファイルのコピー処理を開始 ---")

        # 1. コピー先のフォルダが存在しない場合は作成する
        if not os.path.exists(destination):
            try:
                os.makedirs(destination)
                self.log(f"コピー先フォルダを作成しました: {destination}")
            except OSError as e:
                self.log(f"エラー: コピー先フォルダの作成に失敗しました: {e}")
                messagebox.showerror("エラー", f"フォルダの作成に失敗しました:\n{e}")
                self.copy_button.config(state='normal')
                return

        # 2. プレイリストファイルを読み込む
        try:
            with open(playlist, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            self.log(f"エラー: プレイリストファイルの読み込み中にエラーが発生しました: {e}")
            messagebox.showerror("エラー", f"プレイリストの読み込みに失敗しました:\n{e}")
            self.copy_button.config(state='normal')
            return

        # 3. 各ファイルをコピーする
        copied_count = 0
        skipped_count = 0
        
        for line in lines:
            source_path = line.strip()

            if not source_path or source_path.startswith('#'):
                continue

            if os.path.isfile(source_path):
                original_file_name = os.path.basename(source_path)
                destination_path = os.path.join(destination, original_file_name)
                
                # --- ★★★ここからが変更点★★★ ---
                # コピー先に同名ファイルが存在する場合の処理
                final_file_name = original_file_name
                counter = 1
                while os.path.exists(destination_path):
                    # ファイル名を「名前」と「拡張子」に分割
                    name, ext = os.path.splitext(original_file_name)
                    # 新しいファイル名を生成 (例: "曲名 (1).mp3")
                    final_file_name = f"{name} ({counter}){ext}"
                    destination_path = os.path.join(destination, final_file_name)
                    counter += 1
                # --- ★★★ここまでが変更点★★★ ---

                try:
                    # ファイル名が変更された場合は、その旨をログに記録
                    if final_file_name != original_file_name:
                        self.log(f"コピー中 (名前を変更): {original_file_name} -> {final_file_name}")
                    else:
                        self.log(f"コピー中: {final_file_name}")
                    
                    shutil.copy2(source_path, destination_path)
                    copied_count += 1
                except Exception as e:
                    self.log(f"  -> エラー: ファイルのコピーに失敗しました: {e}")
                    skipped_count += 1
            else:
                self.log(f"スキップ: ファイルが見つかりません: {source_path}")
                skipped_count += 1

        # 4. 結果を表示
        summary = f"""
--- すべての処理が完了しました ---
コピー成功: {copied_count} ファイル
スキップ/失敗: {skipped_count} ファイル
コピー先: '{destination}'
"""
        self.log(summary)
        messagebox.showinfo("完了", "ファイルのコピーが完了しました。")
        self.copy_button.config(state='normal') # ボタンを再度有効化

# スクリプトのメイン処理を実行
if __name__ == '__main__':
    app = PlaylistCopierApp()
    app.mainloop()
