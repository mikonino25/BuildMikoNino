#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Download Manager - Quản lý việc tải manga
"""

import os
import threading
import queue
import time
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class DownloadTask:
    def __init__(self, url, title="", status="Queued"):
        self.url = url
        self.title = title
        self.status = status
        self.progress = 0
        self.chapters = 0
        self.pages = 0
        self.file_size = 0
        self.error = None
        self.current_page = 0
        self.total_pages = 0
        self.retry_count = 0
        self.max_retries = 3
        self.lock = threading.Lock()  # Thread-safe updates
        self.cover_image_url = None  # URL của ảnh bìa
        self.cover_image_data = None  # Dữ liệu ảnh đã download (bytes)
        
class DownloadManager:
    def __init__(self, config_manager, progress_callback=None):
        self.config = config_manager
        self.download_queue = queue.Queue()
        self.active_downloads = {}
        self.download_threads = []
        self.max_concurrent = max(int(self.config.get('Queuing & Error Handling', 'DownloadsMax', '10')), 10)
        self.running = False
        self.progress_callback = progress_callback  # Callback để update UI
        self.all_tasks = {}  # Lưu tất cả tasks để dễ truy cập
        
        # Tạo session với connection pooling để tăng tốc độ
        self.session = requests.Session()
        
        # Cấu hình retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=self.max_concurrent,
            pool_maxsize=self.max_concurrent * 2
        )
        
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Headers mặc định
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def add_download(self, url, title=""):
        """Thêm URL vào danh sách tasks (KHÔNG tự động thêm vào queue - chỉ khi bấm Start)"""
        task = DownloadTask(url, title)
        self.all_tasks[url] = task  # Lưu task để dễ truy cập
        # KHÔNG tự động thêm vào queue - chỉ khi bấm Start mới thêm
        return task
        
    def start_downloads(self):
        """Bắt đầu các thread download"""
        if self.running:
            return
            
        self.running = True
        for i in range(self.max_concurrent):
            thread = threading.Thread(target=self._download_worker, daemon=True)
            thread.start()
            self.download_threads.append(thread)
            
    def stop_downloads(self):
        """Dừng các thread download"""
        self.running = False
        
    def _download_worker(self):
        """Worker thread để xử lý download"""
        while self.running:
            try:
                task = self.download_queue.get(timeout=1)
                if task:
                    self._process_download(task)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Lỗi trong download worker: {e}")
                
    def _update_task_progress(self, task, status=None, progress=None, error=None):
        """Update task progress thread-safe"""
        with task.lock:
            if status:
                task.status = status
            if progress is not None:
                task.progress = progress
            if error:
                task.error = error
                task.status = "Error"
        
        # Gọi callback để update UI
        if self.progress_callback:
            try:
                self.progress_callback(task)
            except:
                pass
    
    def _process_download(self, task):
        """Xử lý một task download với progress real-time"""
        try:
            self._update_task_progress(task, status="Processing", progress=0)
            
            # Tìm module phù hợp cho URL
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            from core.lua_module_loader import LuaModuleLoader
            loader = LuaModuleLoader()
            module = loader.find_module_for_url(task.url)
            
            if not module:
                self._update_task_progress(
                    task, 
                    status="Error", 
                    error="Không tìm thấy module phù hợp cho URL này"
                )
                return
            
            # Nếu task chưa có thông tin, lấy thông tin trước
            with task.lock:
                has_info = task.title and task.pages > 0
            
            if not has_info:
                # Lấy thông tin manga
                self._update_task_progress(task, status="Getting Info", progress=5)
                info = self._get_manga_info(task.url, module)
                
                if info:
                    with task.lock:
                        task.title = info.get('title', task.title)
                        task.chapters = info.get('chapters', 0)
                        task.pages = info.get('pages', 0)
                        task.total_pages = info.get('pages', 0)
            
            # Bắt đầu tải ảnh
            self._update_task_progress(task, status="Downloading", progress=10)
            self._download_manga_images(task, module)
                    
        except requests.exceptions.RequestException as e:
            self._update_task_progress(
                task, 
                status="Error",
                error=f"Lỗi kết nối: {str(e)[:100]}"
            )
        except Exception as e:
            self._update_task_progress(
                task, 
                status="Error",
                error=f"Lỗi: {str(e)[:100]}"
            )
    
    def _download_manga_images(self, task, module):
        """Tải thật các ảnh manga"""
        try:
            # Lấy thư mục download
            download_dir = Path(self.config.get('Directories', 'DownloadDirectory', str(Path.home() / 'Downloads' / 'Manga')))
            
            # Tạo tên thư mục từ title (sanitize)
            with task.lock:
                title = task.title or "Unknown"
            
            # Sanitize tên thư mục
            safe_title = self._sanitize_filename(title)
            manga_dir = download_dir / safe_title
            manga_dir.mkdir(parents=True, exist_ok=True)
            
            # Lấy danh sách ảnh pages (có thể trả về tuple (url, ext) hoặc string)
            page_urls = self._get_page_urls(task.url, module)
            
            if not page_urls:
                # Thử lại với fallback nếu không tìm thấy
                print("⚠ Không tìm thấy ảnh, thử fallback...")
                # Có thể pages đã được set nhưng URL không tạo được
                with task.lock:
                    if task.total_pages > 0:
                        # Đã có số pages, nhưng không tạo được URL
                        self._update_task_progress(task, status="Error", error=f"Đã tìm thấy {task.total_pages} pages nhưng không tạo được URL ảnh")
                    else:
                        self._update_task_progress(task, status="Error", error="Không tìm thấy ảnh nào để tải")
                return
            
            # Xử lý page_urls - có thể là list of strings hoặc list of tuples
            if page_urls and isinstance(page_urls[0], tuple):
                # Đã là tuple (url, ext)
                pass
            else:
                # Convert string URLs thành tuples
                page_urls = [(url, '.jpg') if isinstance(url, str) else url for url in page_urls]
            
            print(f"✓ Tìm thấy {len(page_urls)} URL ảnh để tải")
            
            with task.lock:
                task.total_pages = len(page_urls)
                task.pages = len(page_urls)
            
            # Tải ảnh bìa nếu có
            if task.cover_image_data:
                cover_path = manga_dir / "cover.jpg"
                try:
                    with open(cover_path, 'wb') as f:
                        f.write(task.cover_image_data)
                    print(f"✓ Đã lưu ảnh bìa: {cover_path}")
                except Exception as e:
                    print(f"⚠ Lỗi khi lưu ảnh bìa: {e}")
            
            # Tải từng ảnh page - kiểm tra kích thước thực tế để loại bỏ ảnh bìa/preview
            total_pages = len(page_urls)
            downloaded_size = 0
            saved_count = 0
            
            for idx, page_item in enumerate(page_urls, 1):
                if not self.running or task.status == "Paused":
                    return
                
                try:
                    # Xử lý URL và extension
                    if isinstance(page_item, tuple):
                        page_url, orig_ext = page_item
                    else:
                        page_url = page_item
                        orig_ext = '.jpg'
                    
                    if idx <= 3 or idx % 10 == 0:  # Chỉ log một số ảnh để không spam
                        print(f"Đang tải ảnh {idx}/{total_pages}: {page_url[:80]}...")
                    
                    # Thử tải với extension gốc trước
                    response = None
                    success = False
                    
                    # Thử với extension gốc
                    try:
                        response = self.session.get(page_url, timeout=30, stream=True, allow_redirects=True)
                        if response.status_code == 200:
                            success = True
                    except:
                        pass
                    
                    # Nếu không được, thử với .jpg
                    if not success and orig_ext != '.jpg':
                        jpg_url = page_url.rsplit('.', 1)[0] + '.jpg'
                        try:
                            response = self.session.get(jpg_url, timeout=30, stream=True, allow_redirects=True)
                            if response.status_code == 200:
                                page_url = jpg_url
                                success = True
                        except:
                            pass
                    
                    # Nếu vẫn không được, thử với server khác (chỉ cho HentaiFox)
                    if not success and 'hentaifox.com' in page_url:
                        # Lấy server hiện tại từ URL
                        current_server = None
                        if 'i.hentaifox.com' in page_url:
                            current_server = 'i'
                        elif 'i2.hentaifox.com' in page_url:
                            current_server = 'i2'
                        elif 'i3.hentaifox.com' in page_url:
                            current_server = 'i3'
                        
                        if current_server:
                            for alt_server in ['i', 'i2', 'i3']:
                                if alt_server != current_server:
                                    # Thay server trong URL
                                    alt_url = page_url.replace(f'{current_server}.hentaifox.com', f'{alt_server}.hentaifox.com')
                                    
                                    try:
                                        response = self.session.get(alt_url, timeout=30, stream=True, allow_redirects=True)
                                        if response.status_code == 200:
                                            page_url = alt_url
                                            success = True
                                            print(f"  ✓ Thành công với server {alt_server}")
                                            break
                                    except:
                                        continue
                    
                    if not success or not response or response.status_code != 200:
                        print(f"⚠ Ảnh {idx} không tải được (status: {response.status_code if response else 'N/A'}), bỏ qua")
                        continue
                    
                    response.raise_for_status()
                    
                    # Kiểm tra Content-Type (không quá strict)
                    content_type = response.headers.get('Content-Type', '').lower()
                    if 'image' not in content_type and content_type and 'text' in content_type:
                        print(f"⚠ Ảnh {idx} có Content-Type không phải image: {content_type}, vẫn thử tải...")
                        # Vẫn tiếp tục, có thể server trả về sai Content-Type
                    
                    # Download vào memory để kiểm tra kích thước
                    image_data = b''
                    for chunk in response.iter_content(chunk_size=8192):
                        image_data += chunk
                        # Giới hạn 10MB để tránh memory issue
                        if len(image_data) > 10 * 1024 * 1024:
                            break
                    
                    if len(image_data) == 0:
                        print(f"⚠ Ảnh {idx} rỗng, bỏ qua")
                        continue
                    
                    # Kiểm tra kích thước ảnh thực tế bằng PIL (không quá strict)
                    width, height = 0, 0
                    try:
                        from PIL import Image
                        import io
                        img = Image.open(io.BytesIO(image_data))
                        width, height = img.size
                        print(f"✓ Ảnh {idx}: {width}x{height}, size: {len(image_data)} bytes")
                        
                        # Chỉ bỏ qua nếu quá nhỏ (có thể là lỗi)
                        if width < 100 or height < 100:
                            print(f"⚠ Bỏ qua ảnh {idx}: quá nhỏ ({width}x{height}) - có thể là lỗi")
                            continue
                        
                    except Exception as e:
                        print(f"⚠ Không thể kiểm tra kích thước ảnh {idx}: {e}")
                        # Vẫn lưu nếu không kiểm tra được (có thể là JPG hợp lệ)
                        print(f"  Vẫn lưu ảnh {idx} (không parse được nhưng có thể là ảnh hợp lệ)")
                    
                    # Lưu ảnh với số thứ tự đúng (luôn dùng .jpg)
                    saved_count += 1
                    image_path = manga_dir / f"{saved_count}.jpg"
                    
                    # Nếu không phải JPG, convert về JPG
                    if orig_ext != '.jpg' and width > 0 and height > 0:
                        try:
                            from PIL import Image
                            import io
                            img = Image.open(io.BytesIO(image_data))
                            # Convert về RGB nếu cần (cho PNG có alpha)
                            if img.mode in ('RGBA', 'LA', 'P'):
                                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                                if img.mode == 'P':
                                    img = img.convert('RGBA')
                                rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                                img = rgb_img
                            # Save as JPG
                            img.save(image_path, 'JPEG', quality=95)
                            downloaded_size += image_path.stat().st_size
                        except Exception as e:
                            print(f"⚠ Không thể convert ảnh {idx} về JPG: {e}, lưu trực tiếp...")
                            with open(image_path, 'wb') as f:
                                f.write(image_data)
                                downloaded_size += len(image_data)
                    else:
                        with open(image_path, 'wb') as f:
                            f.write(image_data)
                            downloaded_size += len(image_data)
                    
                    # Update progress
                    with task.lock:
                        task.current_page = saved_count
                        task.file_size = downloaded_size
                    
                    progress = 20 + int((saved_count / total_pages) * 80) if total_pages > 0 else 100
                    self._update_task_progress(task, progress=progress)
                    
                    size_info = f"({width}x{height})" if width > 0 and height > 0 else ""
                    print(f"✓ Đã tải ảnh {saved_count}/{total_pages}: {image_path.name} {size_info}")
                    
                except Exception as e:
                    print(f"⚠ Lỗi khi tải ảnh {idx}: {e}")
                    # Tiếp tục với ảnh tiếp theo
                    continue
            
            # Update total pages với số ảnh thực tế đã lưu
            with task.lock:
                task.total_pages = saved_count
                task.pages = saved_count
            
            # Hoàn thành
            self._update_task_progress(task, status="Completed", progress=100)
            with task.lock:
                task.current_page = total_pages
                task.file_size = downloaded_size
            
            print(f"✓ Hoàn thành tải {total_pages} ảnh vào: {manga_dir}")
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._update_task_progress(task, status="Error", error=str(e)[:100])
    
    def _sanitize_filename(self, filename):
        """Làm sạch tên file để dùng làm tên thư mục"""
        import re
        # Loại bỏ các ký tự không hợp lệ
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # Loại bỏ khoảng trắng thừa
        filename = ' '.join(filename.split())
        # Giới hạn độ dài
        if len(filename) > 200:
            filename = filename[:200]
        return filename or "Unknown"
    
    def _get_image_extension(self, response, url):
        """Luôn trả về .jpg vì chỉ tải JPG"""
        return '.jpg'
    
    def _is_jpg_url(self, url):
        """Kiểm tra xem URL có phải là ảnh JPG không"""
        url_lower = url.lower()
        return url_lower.endswith('.jpg') or url_lower.endswith('.jpeg') or '.jpg' in url_lower or '.jpeg' in url_lower
    
    def _get_page_urls(self, url, module):
        """Lấy danh sách URL của các ảnh pages từ reader/viewer"""
        try:
            # Đọc HTML
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            content = response.content[:1000000]  # Đọc 1MB để có đủ JavaScript
            soup = BeautifulSoup(content, 'html.parser')
            
            # Pattern 1: Tìm reader URL và parse theo cách của HentaiFox
            if 'hentaifox.com' in url:
                reader_url = self._find_reader_url_hentaifox(url, soup)
                if reader_url:
                    print(f"✓ Tìm thấy reader URL: {reader_url}")
                    page_urls = self._parse_hentaifox_pages(reader_url)
                    if page_urls and len(page_urls) > 0:
                        print(f"✓ Parse HentaiFox thành công: {len(page_urls)} ảnh")
                        return page_urls
                    else:
                        print(f"⚠ Parse HentaiFox không tạo được URL ảnh (đã parse được JSON nhưng không tạo được URL)")
                else:
                    print("⚠ Không tìm thấy reader URL cho HentaiFox")
            
            # Pattern 2: Tìm reader URL thông thường
            if not reader_url:
                reader_url = self._find_reader_url(url, soup)
            
            if reader_url:
                # Lấy danh sách ảnh từ reader page
                reader_response = self.session.get(reader_url, timeout=15)
                reader_content = reader_response.content[:1000000]
                reader_soup = BeautifulSoup(reader_content, 'html.parser')
                
                # Chỉ lấy ảnh từ reader/viewer area, không lấy ảnh bìa
                page_urls = self._extract_images_from_reader_area(reader_url, reader_soup)
                
                if page_urls:
                    return page_urls
            
            # Pattern 3: Parse JavaScript để lấy danh sách ảnh
            page_urls = self._parse_images_from_javascript(content, url)
            if page_urls:
                return page_urls
            
            # Pattern 4: Tìm trong reader area của trang hiện tại
            page_urls = self._extract_images_from_reader_area(url, soup)
            
            # Loại bỏ duplicate và chỉ lấy JPG
            seen = set()
            unique_urls = []
            for img_url in page_urls:
                if img_url and img_url not in seen and img_url.startswith('http'):
                    # Chỉ lấy ảnh JPG
                    if self._is_jpg_url(img_url):
                        seen.add(img_url)
                        unique_urls.append(img_url)
            
            return unique_urls
            
        except Exception as e:
            print(f"Lỗi khi lấy danh sách ảnh: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _find_reader_url_hentaifox(self, url, soup):
        """Tìm reader URL theo cách của HentaiFox"""
        from urllib.parse import urljoin
        
        # Pattern 1: Tìm button với class g_button (theo module Lua)
        button = soup.find('a', class_=lambda x: x and 'g_button' in str(x))
        if button:
            href = button.get('href')
            if href:
                reader_url = urljoin(url, href)
                print(f"✓ Tìm thấy g_button: {reader_url}")
                return reader_url
        
        # Pattern 2: Tìm link "Read Online" (text chính xác hoặc chứa)
        read_online = soup.find('a', string=lambda x: x and 'read' in x.lower() and 'online' in x.lower())
        if read_online:
            href = read_online.get('href')
            if href:
                reader_url = urljoin(url, href)
                print(f"✓ Tìm thấy Read Online link: {reader_url}")
                return reader_url
        
        # Pattern 3: Tìm tất cả link có text chứa "Read" và href có /g/
        read_links = soup.find_all('a', href=True)
        for link in read_links:
            link_text = link.get_text().strip().lower()
            href = link.get('href')
            if href and ('read' in link_text or 'online' in link_text):
                if '/g/' in href or '/gallery/' in href:
                    reader_url = urljoin(url, href)
                    print(f"✓ Tìm thấy Read link: {reader_url}")
                    return reader_url
        
        # Pattern 4: Tìm link có href chứa /g/ và không phải gallery page
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link.get('href')
            if href and '/g/' in href and '/gallery/' not in href:
                # Có thể là reader URL
                reader_url = urljoin(url, href)
                print(f"✓ Tìm thấy /g/ link: {reader_url}")
                return reader_url
        
        print("⚠ Không tìm thấy reader URL")
        return None
    
    def _parse_hentaifox_pages(self, reader_url):
        """Parse ảnh pages từ HentaiFox reader page theo đúng chuẩn HentaiFox.lua GetPages()"""
        try:
            import re
            import json
            import random
            
            print(f"Đang parse HentaiFox reader: {reader_url}")
            response = self.session.get(reader_url, timeout=15)
            response.raise_for_status()
            content = response.text
            
            # Parse các giá trị từ input fields theo module Lua
            # dom.SelectValue('//input[@name="image_dir"]/@value')
            soup = BeautifulSoup(content, 'html.parser')
            
            image_dir_input = soup.find('input', {'name': 'image_dir'})
            gallery_id_input = soup.find('input', {'name': 'gallery_id'})
            unique_id_input = soup.find('input', {'name': 'unique_id'})
            
            if not image_dir_input or not gallery_id_input:
                print("⚠ Không tìm thấy image_dir hoặc gallery_id trong reader page")
                return []
            
            image_dir = image_dir_input.get('value', '').strip()
            gallery_id = gallery_id_input.get('value', '').strip()
            unique_id = int(unique_id_input.get('value', '0')) if unique_id_input else 0
            
            # Validate
            if not image_dir or not gallery_id:
                print(f"⚠ image_dir hoặc gallery_id rỗng: image_dir='{image_dir}', gallery_id='{gallery_id}'")
                return []
            
            print(f"✓ Found: image_dir={image_dir}, gallery_id={gallery_id}, unique_id={unique_id}")
            
            # Parse JavaScript JSON theo module Lua
            # tostring(dom):regex("var\\s*g_th\\s*=\\s*\\$\\.parseJSON\\('(.+?)'\\);", 1)
            json_pattern = r"var\s+g_th\s*=\s*\$\.parseJSON\('(.+?)'\);"
            json_match = re.search(json_pattern, content, re.DOTALL)
            
            if not json_match:
                # Thử pattern khác
                json_patterns = [
                    r"var\s+g_th\s*=\s*JSON\.parse\('(.+?)'\);",
                    r"g_th\s*=\s*\$\.parseJSON\('(.+?)'\);",
                    r"g_th\s*=\s*JSON\.parse\('(.+?)'\);",
                ]
                for pattern in json_patterns:
                    json_match = re.search(pattern, content, re.DOTALL)
                    if json_match:
                        break
            
            if not json_match:
                print("⚠ Không tìm thấy g_th JSON trong reader page")
                return []
            
            try:
                thumbnails_json_str = json_match.group(1)
                # Unescape JSON string
                thumbnails_json_str = thumbnails_json_str.replace('\\"', '"').replace("\\'", "'")
                thumbnails_json_str = thumbnails_json_str.replace('\\/', '/')
                thumbnails = json.loads(thumbnails_json_str)
                print(f"✓ Parsed JSON với {len(thumbnails)} pages")
            except Exception as e:
                print(f"⚠ Lỗi parse JSON: {e}")
                return []
            
            # Xác định image server theo module Lua
            # local imageServers = { "i", "i2" }
            # local imageServer = imageServers[math.random(1, #imageServers)]
            # if not uniqueId or uniqueId > 140236 then imageServer = "i3" end
            if unique_id > 140236:
                image_server = "i3"
            else:
                image_servers = ["i", "i2"]
                image_server = random.choice(image_servers)
            
            # Tạo danh sách URL ảnh theo module Lua
            # FormatString('//{0}.{1}/{2}/{3}/{4}{5}', imageServer, module.Domain, imageDir, galleryId, pageNumber, pageExtension)
            page_urls = []
            domain = "hentaifox.com"
            
            # Sắp xếp keys theo số
            sorted_keys = sorted(thumbnails.keys(), key=lambda x: int(x) if str(x).isdigit() else 0)
            
            print(f"✓ Đã parse {len(sorted_keys)} pages từ JSON, bắt đầu tạo URL...")
            
            for page_num in sorted_keys:
                # Đảm bảo page_num là string
                page_num_str = str(page_num).strip()
                if not page_num_str or not page_num_str.isdigit():
                    print(f"⚠ Bỏ qua page_num không hợp lệ: {page_num}")
                    continue
                
                # Lấy extension code từ JSON theo module Lua
                ext_code_str = thumbnails[page_num]
                if isinstance(ext_code_str, str):
                    ext_code = ext_code_str.split(',')[0].strip()
                else:
                    ext_code = 'j'
                
                # Convert extension code theo module Lua
                if ext_code == 'p':
                    ext = '.png'
                elif ext_code == 'g':
                    ext = '.gif'
                elif ext_code == 'w':
                    ext = '.webp'
                else:
                    ext = '.jpg'
                
                # Tạo URL với extension đúng
                # Format: https://{server}.{domain}/{image_dir}/{gallery_id}/{page_num}{ext}
                img_url = f"https://{image_server}.{domain}/{image_dir}/{gallery_id}/{page_num_str}{ext}"
                page_urls.append((img_url, ext))  # Lưu cả extension để biết format
            
            if len(page_urls) == 0:
                print(f"⚠ Không tạo được URL nào từ {len(sorted_keys)} pages!")
                print(f"   image_dir={image_dir}, gallery_id={gallery_id}, image_server={image_server}")
            else:
                jpg_count = sum(1 for _, ext in page_urls if ext == '.jpg')
                print(f"✓ Tạo được {len(page_urls)} URL ảnh từ {len(sorted_keys)} pages (JPG: {jpg_count})")
                print(f"   Ví dụ URL đầu tiên: {page_urls[0][0] if page_urls else 'N/A'}")
            
            return page_urls
            
        except Exception as e:
            print(f"Lỗi khi parse HentaiFox pages: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _find_reader_url(self, url, soup):
        """Tìm URL của reader page"""
        # Tìm link "Read" hoặc "View"
        read_links = soup.find_all('a', href=True, string=lambda x: x and ('read' in x.lower() or 'view' in x.lower() or 'online' in x.lower()))
        for link in read_links:
            href = link.get('href')
            if href:
                from urllib.parse import urljoin
                return urljoin(url, href)
        
        # Tìm button với class chứa "read" hoặc "view"
        buttons = soup.find_all(['a', 'button'], class_=lambda x: x and ('read' in str(x).lower() or 'view' in str(x).lower()))
        for btn in buttons:
            href = btn.get('href')
            if href:
                from urllib.parse import urljoin
                return urljoin(url, href)
        
        return None
    
    def _parse_images_from_javascript(self, content, url):
        """Parse danh sách ảnh từ JavaScript trong HTML"""
        try:
            import re
            import json
            
            # Tìm JSON array chứa images
            patterns = [
                r'"images"\s*:\s*(\[[^\]]+\])',
                r'images\s*=\s*(\[[^\]]+\])',
                r'var\s+images\s*=\s*(\[[^\]]+\])',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    try:
                        images_json = json.loads(match.group(1))
                        page_urls = []
                        for img_url in images_json:
                            if isinstance(img_url, str) and self._is_jpg_url(img_url):
                                from urllib.parse import urljoin
                                if not img_url.startswith('http'):
                                    img_url = urljoin(url, img_url)
                                page_urls.append(img_url)
                        if page_urls:
                            return page_urls
                    except:
                        continue
            
            return []
        except Exception as e:
            print(f"Lỗi khi parse JavaScript: {e}")
            return []
    
    def _extract_images_from_reader_area(self, base_url, soup):
        """Trích xuất ảnh chỉ từ reader/viewer area, không lấy ảnh bìa"""
        page_urls = []
        
        # Tìm reader/viewer container - ưu tiên các selector cụ thể
        reader_selectors = [
            '#readerarea img',
            '#reader img',
            '.reader img',
            '.viewer img',
            '#viewer img',
            '#image-container img',
            '.image-container img',
            '#chapter-images img',
            '.chapter-images img',
            '#pages img',
            '.pages img',
            '[id*="reader"] img',
            '[class*="reader"] img',
            '[id*="viewer"] img',
            '[class*="viewer"] img',
        ]
        
        # Tìm ảnh trong reader area cụ thể
        reader_imgs = []
        for selector in reader_selectors:
            imgs = soup.select(selector)
            if imgs:
                reader_imgs = imgs
                break
        
        # Nếu không tìm thấy, tìm trong toàn bộ trang nhưng filter rất kỹ
        if not reader_imgs:
            reader_imgs = soup.find_all('img')
        
        # Từ khóa để skip (mở rộng)
        skip_keywords = [
            'icon', 'logo', 'avatar', 'button', 'banner', 'ad', 'ads',
            'thumbnail', 'thumb', 'cover', 'poster', 'preview', 'sample',
            'small', 'mini', 'tiny', 'related', 'similar', 'recommend',
            'gallery', 'gallery-', 'g_', 'thumb_', 'thumb-', 't_',
            'header', 'footer', 'sidebar', 'nav', 'menu'
        ]
        
        # Tìm ảnh trong reader area
        for img in reader_imgs:
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src') or img.get('data-original')
            if not src:
                continue
            
            # Convert relative URL to absolute
            from urllib.parse import urljoin
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('/'):
                src = urljoin(base_url, src)
            elif not src.startswith('http'):
                src = urljoin(base_url, src)
            
            if not src.startswith('http') or not self._is_jpg_url(src):
                continue
            
            src_lower = src.lower()
            
            # Kiểm tra URL - skip nếu chứa từ khóa
            if any(keyword in src_lower for keyword in skip_keywords):
                continue
            
            # Kiểm tra parent elements - skip nếu trong container có từ khóa
            parent = img.parent
            parent_class = ''
            parent_id = ''
            for _ in range(3):  # Check 3 levels up
                if parent:
                    parent_class = str(parent.get('class', '')).lower()
                    parent_id = str(parent.get('id', '')).lower()
                    if any(keyword in parent_class or keyword in parent_id for keyword in skip_keywords):
                        break
                    parent = parent.parent
                else:
                    break
            else:
                continue  # Found skip keyword in parent
            
            # Kiểm tra kích thước ảnh
            width = img.get('width')
            height = img.get('height')
            if width and height:
                try:
                    w, h = int(width), int(height)
                    # Bỏ qua ảnh quá nhỏ (thumbnail thường < 300px)
                    if w < 300 or h < 300:
                        continue
                except:
                    pass
            
            # Kiểm tra class/id của img
            img_class = str(img.get('class', '')).lower()
            img_id = str(img.get('id', '')).lower()
            
            if any(keyword in img_class or keyword in img_id for keyword in skip_keywords):
                continue
            
            # Kiểm tra pattern URL - ảnh bìa thường có pattern khác
            # Ảnh pages thường có số trong URL hoặc path cụ thể
            url_path = src_lower.split('?')[0]  # Remove query params
            
            # Skip nếu URL có vẻ là thumbnail/cover (có thể có pattern như thumb, cover, etc)
            if '/thumb' in url_path or '/cover' in url_path or '/preview' in url_path:
                continue
            
            # Chỉ lấy ảnh có vẻ là page (có số trong path hoặc tên file)
            import re
            # Kiểm tra xem có số trong path không (thường ảnh page có số)
            has_number_in_path = bool(re.search(r'/\d+\.jpg|/\d+\.jpeg|page\d+|p\d+|_\d+\.jpg', url_path))
            
            # Hoặc ảnh từ image server (như hentaifox: i.hentaifox.com/image_dir/gallery_id/1.jpg)
            is_image_server = bool(re.search(r'/(i\d*|cdn|img|images|static)/', url_path))
            
            # Nếu không có số và không phải image server, có thể là ảnh bìa
            if not has_number_in_path and not is_image_server:
                # Kiểm tra thêm: nếu URL ngắn hoặc có pattern đặc biệt, có thể là bìa
                if len(url_path.split('/')) < 5:  # URL ngắn thường là bìa
                    continue
            
            page_urls.append(src)
        
        return page_urls
    
            
    def _get_manga_info(self, url, module):
        """Lấy thông tin manga từ URL theo chuẩn module Lua"""
        try:
            # Sử dụng session để tái sử dụng connection
            response = self.session.get(url, timeout=20, stream=True, allow_redirects=True)
            response.raise_for_status()
            
            content = response.content[:500000]  # Đọc 500KB để có đủ thông tin
            soup = BeautifulSoup(content, 'html.parser')
            
            # Parse theo module HentaiFox.lua GetInfo()
            info = {}
            
            # Title: //h1
            h1 = soup.find('h1')
            if h1:
                title_text = h1.get_text().strip()
                # Làm sạch title
                title_text = title_text.replace('\n', ' ').replace('\r', ' ')
                title_text = ' '.join(title_text.split())  # Loại bỏ khoảng trắng thừa
                # Loại bỏ các ký tự không hợp lệ cho filename
                title_text = ''.join(c for c in title_text if c.isprintable() or c in ' -_')
                info['title'] = title_text[:200]
            else:
                # Fallback: dùng title tag
                title_tag = soup.find('title')
                if title_tag:
                    title_text = title_tag.get_text().strip()
                    # Loại bỏ suffix như " - HentaiFox"
                    title_text = title_text.split(' - ')[0].split(' | ')[0]
                    info['title'] = title_text[:200]
                else:
                    from urllib.parse import urlparse
                    parsed = urlparse(url)
                    info['title'] = parsed.path.split('/')[-1] or url[:50]
            
            # PageCount: //span[contains(@class, "pages")] sau dấu ":"
            pages = 0
            if 'hentaifox.com' in url:
                # Theo HentaiFox.lua: getPageCount()
                page_spans = soup.find_all('span', class_=lambda x: x and 'pages' in str(x).lower())
                for span in page_spans:
                    text = span.get_text().strip()
                    if ':' in text:
                        try:
                            # Lấy số sau dấu ":"
                            page_text = text.split(':')[-1].strip()
                            import re
                            match = re.search(r'(\d+)', page_text)
                            if match:
                                pages = int(match.group(1))
                                break
                        except:
                            pass
                
                # Fallback: tìm "Pages: 36" trong text
                if pages == 0:
                    page_elements = soup.find_all(string=lambda x: x and 'pages' in x.lower() and ':' in x.lower())
                    for elem in page_elements:
                        import re
                        match = re.search(r'pages?\s*:\s*(\d+)', elem, re.IGNORECASE)
                        if match:
                            pages = int(match.group(1))
                            break
            
            # Nếu không tìm thấy, tìm pattern chung
            if pages == 0:
                page_elements = soup.find_all(['span', 'div', 'p'], string=lambda x: x and 'page' in x.lower())
                for elem in page_elements[:10]:
                    text = elem.get_text().lower()
                    import re
                    match = re.search(r'(\d+)\s*pages?', text)
                    if match:
                        pages = int(match.group(1))
                        break
            
            info['pages'] = pages if pages > 0 else 1
            info['chapters'] = 1  # Mặc định 1 chapter cho gallery
            
            return info
            
        except requests.exceptions.Timeout:
            raise Exception("Timeout khi kết nối đến server")
        except requests.exceptions.ConnectionError:
            raise Exception("Không thể kết nối đến server")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"Lỗi HTTP {e.response.status_code}: {e.response.reason}")
        except Exception as e:
            raise Exception(f"Lỗi khi lấy thông tin: {str(e)[:50]}")
        
    def add_multiple_downloads(self, urls):
        """Thêm nhiều URLs cùng lúc"""
        tasks = []
        for url in urls:
            task = self.add_download(url)
            tasks.append(task)
        return tasks
        
    def pause_download(self, task):
        """Tạm dừng download"""
        task.status = "Paused"
        
    def resume_download(self, task):
        """Tiếp tục download"""
        if task.status == "Paused":
            task.status = "Queued"
            self.download_queue.put(task)
            
    def remove_download(self, task):
        """Xóa download khỏi hàng đợi"""
        task.status = "Removed"

