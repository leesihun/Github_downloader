#!/usr/bin/env python3
"""
Build script for creating ETX Dashboard executable
"""
import os
import sys
import subprocess
import shutil

def check_requirements():
    """Check if all requirements are met"""
    print("🔍 Checking build requirements...")
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print("✅ PyInstaller found")
    except ImportError:
        print("❌ PyInstaller not found")
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✅ PyInstaller installed")
    
    # Check if spec file exists
    if not os.path.exists("ETX_Dashboard.spec"):
        print("❌ ETX_Dashboard.spec not found")
        return False
    
    print("✅ All requirements met")
    return True

def clean_build():
    """Clean previous build artifacts"""
    print("🧹 Cleaning previous build artifacts...")
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✅ Removed {dir_name}")
    
    print("✅ Build directory cleaned")

def build_executable():
    """Build the executable"""
    print("🔨 Building executable...")
    
    try:
        # Run PyInstaller with the spec file
        result = subprocess.run([
            sys.executable, "-m", "PyInstaller", 
            "ETX_Dashboard.spec", 
            "--clean", 
            "--noconfirm"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Build completed successfully!")
            
            # Check if executable exists
            exe_path = os.path.join("dist", "ETX_Dashboard.exe")
            if os.path.exists(exe_path):
                size_mb = os.path.getsize(exe_path) / (1024 * 1024)
                print(f"📁 Executable created: {exe_path} ({size_mb:.1f} MB)")
                return True
            else:
                print("❌ Executable not found in dist folder")
                return False
        else:
            print("❌ Build failed!")
            print("Error output:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Build error: {e}")
        return False

def main():
    """Main build process"""
    print("🚀 ETX Dashboard Build Script")
    print("=" * 40)
    
    # Check requirements
    if not check_requirements():
        print("❌ Build requirements not met")
        return False
    
    # Clean previous build
    clean_build()
    
    # Build executable
    if build_executable():
        print("\n" + "=" * 40)
        print("✅ Build completed successfully!")
        print("📁 Executable location: dist/ETX_Dashboard.exe")
        print("🎉 You can now run the standalone executable!")
        return True
    else:
        print("\n" + "=" * 40)
        print("❌ Build failed!")
        print("🔧 Please check the error messages above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 