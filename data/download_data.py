"""
Smart Data Downloader - Downloads ONLY files referenced in JSON
Uses rclone to download from Google Drive to Vast.ai
"""

import json
import os
import subprocess
from tqdm import tqdm
from pathlib import Path

class SmartDownloader:
    def __init__(self, gdrive_path='gdrive:CropNet', local_path='/workspace/CropNet'):
        self.gdrive_path = gdrive_path
        self.local_path = local_path
        self.files_to_download = set()
    
    def extract_files_from_json(self, json_path):
        """Extract all file paths from JSON"""
        print(f"📋 Reading {json_path}...")
        
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        print(f"✅ Found {len(data)} samples")
        
        for sample in data:
            # USDA file
            self.files_to_download.add(sample['data']['USDA'])
            
            # Sentinel files
            for s in sample['data']['sentinel']:
                self.files_to_download.add(s)
            
            # HRRR short term
            for h in sample['data']['HRRR']['short_term']:
                self.files_to_download.add(h)
            
            # HRRR long term
            for year_data in sample['data']['HRRR']['long_term']:
                for h in year_data:
                    self.files_to_download.add(h)
        
        print(f"✅ Total unique files: {len(self.files_to_download)}")
    
    def download_files(self):
        """Download files using rclone"""
        print("\n" + "=" * 70)
        print("DOWNLOADING FILES FROM GOOGLE DRIVE")
        print("=" * 70)
        print(f"Source: {self.gdrive_path}")
        print(f"Destination: {self.local_path}")
        print(f"Files to download: {len(self.files_to_download)}")
        print("")
        
        # Create base directory
        os.makedirs(self.local_path, exist_ok=True)
        
        downloaded = 0
        failed = 0
        
        for file_path in tqdm(sorted(self.files_to_download), desc="Downloading"):
            # Create parent directory
            local_file = os.path.join(self.local_path, file_path)
            parent_dir = os.path.dirname(local_file)
            os.makedirs(parent_dir, exist_ok=True)
            
            # Skip if already exists
            if os.path.exists(local_file):
                downloaded += 1
                continue
            
            # Download with rclone
            remote_file = f"{self.gdrive_path}/{file_path}"
            
            try:
                result = subprocess.run(
                    ['rclone', 'copy', remote_file, parent_dir, '--quiet'],
                    capture_output=True,
                    timeout=300  # 5 minute timeout per file
                )
                
                if result.returncode == 0:
                    downloaded += 1
                else:
                    failed += 1
                    print(f"\n⚠️  Failed: {file_path}")
            
            except subprocess.TimeoutExpired:
                failed += 1
                print(f"\n⚠️  Timeout: {file_path}")
            except Exception as e:
                failed += 1
                print(f"\n⚠️  Error downloading {file_path}: {e}")
        
        print("\n" + "=" * 70)
        print(f"✅ Downloaded: {downloaded}")
        print(f"❌ Failed: {failed}")
        print("=" * 70)
    
    def verify_downloads(self):
        """Verify all files were downloaded"""
        print("\n" + "=" * 70)
        print("VERIFYING DOWNLOADS")
        print("=" * 70)
        
        missing = []
        
        for file_path in self.files_to_download:
            local_file = os.path.join(self.local_path, file_path)
            
            # Check for nested .h5 files
            if os.path.isdir(local_file):
                local_file = os.path.join(local_file, os.path.basename(local_file))
            
            if not os.path.exists(local_file):
                missing.append(file_path)
        
        if missing:
            print(f"❌ Missing {len(missing)} files:")
            for f in missing[:10]:
                print(f"  - {f}")
            if len(missing) > 10:
                print(f"  ... and {len(missing) - 10} more")
            return False
        else:
            print(f"✅ All {len(self.files_to_download)} files downloaded successfully!")
            return True

def main():
    print("=" * 70)
    print("SMART DATA DOWNLOADER - Download Only What You Need")
    print("=" * 70)
    print("")
    
    # Check rclone is available
    try:
        subprocess.run(['rclone', 'version'], capture_output=True, check=True)
        print("✅ rclone is installed")
    except:
        print("❌ rclone not found! Please install it first:")
        print("   curl https://rclone.org/install.sh | sudo bash")
        return
    
    # Check JSON files exist
    if not os.path.exists('soybean_train.json'):
        print("❌ soybean_train.json not found!")
        print("   Please upload it to current directory first")
        return
    
    if not os.path.exists('soybean_test.json'):
        print("❌ soybean_test.json not found!")
        print("   Please upload it to current directory first")
        return
    
    # Create downloader
    downloader = SmartDownloader(
        gdrive_path='gdrive:CropNet',
        local_path='/workspace/CropNet'
    )
    
    # Extract files from JSONs
    downloader.extract_files_from_json('soybean_train.json')
    downloader.extract_files_from_json('soybean_test.json')
    
    print(f"\n📊 Download Summary:")
    print(f"  Total unique files: {len(downloader.files_to_download)}")
    
    # Estimate size (rough estimate)
    num_sentinel = sum(1 for f in downloader.files_to_download if '.h5' in f)
    num_hrrr = sum(1 for f in downloader.files_to_download if 'HRRR' in f)
    num_usda = sum(1 for f in downloader.files_to_download if 'USDA' in f)
    
    estimated_size = (num_sentinel * 15) + (num_hrrr * 0.5) + (num_usda * 0.001)
    
    print(f"  Sentinel files: {num_sentinel} (~{num_sentinel * 15:.0f} MB)")
    print(f"  HRRR files: {num_hrrr} (~{num_hrrr * 0.5:.0f} MB)")
    print(f"  USDA files: {num_usda} (~{num_usda * 0.001:.1f} MB)")
    print(f"  Estimated total: ~{estimated_size / 1024:.1f} GB")
    print("")
    
    # Ask for confirmation
    response = input("Start download? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Download cancelled.")
        return
    
    # Download
    downloader.download_files()
    
    # Verify
    success = downloader.verify_downloads()
    
    if success:
        print("\n✅ All files downloaded successfully!")
        print("✅ Ready to run verify_data.py")
    else:
        print("\n⚠️  Some files missing. You may need to:")
        print("  1. Check your rclone configuration")
        print("  2. Re-run this script")
        print("  3. Manually download missing files")

if __name__ == '__main__':
    main()