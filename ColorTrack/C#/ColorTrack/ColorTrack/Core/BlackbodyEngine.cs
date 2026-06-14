using System;
using System.Drawing;
using System.IO;

namespace ColorTrack.Core
{
    /// <summary>
    /// 배경 이미지 로더 클래스
    /// </summary>
    public static class BackgroundImageLoader
    {
        /// <summary>
        /// CIE 1931 배경 이미지 로드
        /// </summary>
        public static Image LoadCie1931Background()
        {
            var possiblePaths = new[]
            {
                "cie1931_background_clean.png",
                @"C:\non_documents\ColorTrack\cie1931_background_clean.png",
                Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "Images", "cie1931_background_clean.png"),
                Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "cie1931_background_clean.png")
            };

            foreach (var path in possiblePaths)
            {
                if (File.Exists(path))
                {
                    try
                    {
                        return Image.FromFile(path);
                    }
                    catch (Exception ex)
                    {
                        System.Diagnostics.Debug.WriteLine($"Failed to load CIE 1931 background from {path}: {ex.Message}");
                    }
                }
            }

            System.Diagnostics.Debug.WriteLine("CIE 1931 background image not found");
            return null;
        }

        /// <summary>
        /// CIE 1976 배경 이미지 로드
        /// </summary>
        public static Image LoadCie1976Background()
        {
            var possiblePaths = new[]
            {
                "cie1976_background_clean.png",
                @"C:\non_documents\ColorTrack\cie1976_background_clean.png",
                Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "Images", "cie1976_background_clean.png"),
                Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "cie1976_background_clean.png")
            };

            foreach (var path in possiblePaths)
            {
                if (File.Exists(path))
                {
                    try
                    {
                        return Image.FromFile(path);
                    }
                    catch (Exception ex)
                    {
                        System.Diagnostics.Debug.WriteLine($"Failed to load CIE 1976 background from {path}: {ex.Message}");
                    }
                }
            }

            System.Diagnostics.Debug.WriteLine("CIE 1976 background image not found");
            return null;
        }

        /// <summary>
        /// 이미지가 로드되었는지 확인
        /// </summary>
        public static bool IsImageLoaded(Image image)
        {
            return image != null;
        }

        /// <summary>
        /// 이미지 리소스 해제
        /// </summary>
        public static void DisposeImage(ref Image image)
        {
            if (image != null)
            {
                image.Dispose();
                image = null;
            }
        }

        /// <summary>
        /// 기본 배경 이미지 생성 (이미지 로드 실패 시 사용)
        /// </summary>
        public static Bitmap CreateDefaultBackground(int width, int height, Color backgroundColor)
        {
            var bitmap = new Bitmap(width, height);
            using (var graphics = Graphics.FromImage(bitmap))
            {
                graphics.Clear(backgroundColor);

                // 간단한 그리드 패턴 추가
                using (var pen = new Pen(Color.FromArgb(50, Color.Gray), 1))
                {
                    // 세로선
                    for (int x = 0; x < width; x += 50)
                    {
                        graphics.DrawLine(pen, x, 0, x, height);
                    }

                    // 가로선
                    for (int y = 0; y < height; y += 50)
                    {
                        graphics.DrawLine(pen, 0, y, width, y);
                    }
                }
            }
            return bitmap;
        }

        /// <summary>
        /// CIE 1931용 기본 배경 생성
        /// </summary>
        public static Bitmap CreateDefaultCie1931Background(int width = 800, int height = 900)
        {
            return CreateDefaultBackground(width, height, Color.FromArgb(248, 248, 255)); // AliceBlue
        }

        /// <summary>
        /// CIE 1976용 기본 배경 생성
        /// </summary>
        public static Bitmap CreateDefaultCie1976Background(int width = 700, int height = 600)
        {
            return CreateDefaultBackground(width, height, Color.FromArgb(255, 248, 248)); // MistyRose
        }
    }
}