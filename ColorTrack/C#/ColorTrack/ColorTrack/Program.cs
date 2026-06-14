using System;
using System.Windows.Forms;

namespace ColorTrack
{
    /// <summary>
    /// ColorTrack 애플리케이션의 진입점
    /// </summary>
    internal static class Program
    {
        /// <summary>
        /// 애플리케이션의 주 진입점입니다.
        /// </summary>
        [STAThread]
        static void Main()
        {
            // Windows Forms 애플리케이션 설정
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);

            try
            {
                // 메인 폼 생성 및 실행
                using (var mainForm = new MainForm())
                {
                    Application.Run(mainForm);
                }
            }
            catch (Exception ex)
            {
                // 예외 처리
                MessageBox.Show(
                    $"애플리케이션 실행 중 오류가 발생했습니다:\n\n{ex.Message}\n\n상세 정보:\n{ex.StackTrace}",
                    "ColorTrack - 오류",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error);
            }
        }
    }
}