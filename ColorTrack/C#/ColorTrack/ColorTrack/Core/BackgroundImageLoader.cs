using System;
using System.Collections.Generic;
using System.Drawing;
using System.Windows.Forms;

namespace ColorTrack
{
    public partial class SettingsForm : Form
    {
        public bool ShowBackground { get; set; }
        public bool ShowBoundaries { get; set; }
        public int BackgroundAlpha { get; set; }
        public Dictionary<int, bool> BlackbodyIntervals { get; set; }

        private CheckBox _showBackgroundCheckBox;
        private CheckBox _showBoundariesCheckBox;
        private TrackBar _alphaTrackBar;
        private Label _alphaLabel;
        private CheckBox[] _blackbodyCheckBoxes;

        public SettingsForm()
        {
            InitializeComponent();
            BlackbodyIntervals = new Dictionary<int, bool>();
        }

        private void InitializeComponent()
        {
            this.Text = "설정";
            this.Size = new Size(350, 300);
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.MaximizeBox = false;
            this.MinimizeBox = false;
            this.StartPosition = FormStartPosition.CenterParent;

            var mainPanel = new TableLayoutPanel
            {
                Dock = DockStyle.Fill,
                RowCount = 6,
                ColumnCount = 1,
                Padding = new Padding(20)
            };

            // 좌표계색보기 체크박스
            _showBackgroundCheckBox = new CheckBox
            {
                Text = "좌표계색보기",
                Font = new Font("Segoe UI", 10),
                Dock = DockStyle.Fill,
                AutoSize = true
            };

            // 색좌표경계 체크박스
            _showBoundariesCheckBox = new CheckBox
            {
                Text = "색좌표경계",
                Font = new Font("Segoe UI", 10),
                Dock = DockStyle.Fill,
                AutoSize = true
            };

            // Blackbody Locus 라벨
            var blackbodyLabel = new Label
            {
                Text = "Blackbody Locus Intervals:",
                Font = new Font("Segoe UI", 10, FontStyle.Bold),
                Dock = DockStyle.Fill,
                AutoSize = true
            };

            // Blackbody 체크박스들을 위한 패널
            var blackbodyPanel = new FlowLayoutPanel
            {
                Dock = DockStyle.Fill,
                FlowDirection = FlowDirection.LeftToRight,
                WrapContents = true
            };

            var intervals = new[] { 100, 500, 1000, 1500 };
            _blackbodyCheckBoxes = new CheckBox[intervals.Length];
            for (int i = 0; i < intervals.Length; i++)
            {
                _blackbodyCheckBoxes[i] = new CheckBox
                {
                    Text = $"{intervals[i]}K",
                    Font = new Font("Segoe UI", 10),
                    AutoSize = true,
                    Margin = new Padding(0, 0, 15, 5)
                };
                blackbodyPanel.Controls.Add(_blackbodyCheckBoxes[i]);
            }

            // 투명도 슬라이더
            var alphaPanel = new TableLayoutPanel
            {
                Dock = DockStyle.Fill,
                ColumnCount = 3,
                RowCount = 1
            };
            alphaPanel.ColumnStyles.Add(new ColumnStyle(SizeType.AutoSize));
            alphaPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
            alphaPanel.ColumnStyles.Add(new ColumnStyle(SizeType.AutoSize));

            var alphaLabelText = new Label
            {
                Text = "좌표계색투명도:",
                Font = new Font("Segoe UI", 10),
                AutoSize = true,
                Anchor = AnchorStyles.Left
            };

            _alphaTrackBar = new TrackBar
            {
                Minimum = 10,
                Maximum = 100,
                TickFrequency = 10,
                Dock = DockStyle.Fill
            };
            _alphaTrackBar.ValueChanged += AlphaTrackBar_ValueChanged;

            _alphaLabel = new Label
            {
                Text = "70%",
                Font = new Font("Segoe UI", 10),
                AutoSize = true,
                Anchor = AnchorStyles.Right
            };

            alphaPanel.Controls.Add(alphaLabelText, 0, 0);
            alphaPanel.Controls.Add(_alphaTrackBar, 1, 0);
            alphaPanel.Controls.Add(_alphaLabel, 2, 0);

            // 버튼 패널
            var buttonPanel = new FlowLayoutPanel
            {
                Dock = DockStyle.Fill,
                FlowDirection = FlowDirection.RightToLeft
            };

            var closeButton = new Button
            {
                Text = "닫기",
                Size = new Size(80, 30),
                DialogResult = DialogResult.OK,
                BackColor = Color.FromArgb(74, 144, 226),
                ForeColor = Color.White,
                FlatStyle = FlatStyle.Flat,
                Font = new Font("Segoe UI", 10, FontStyle.Bold)
            };
            closeButton.Click += CloseButton_Click;

            buttonPanel.Controls.Add(closeButton);

            // 행 스타일 설정
            mainPanel.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            mainPanel.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            mainPanel.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            mainPanel.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            mainPanel.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            mainPanel.RowStyles.Add(new RowStyle(SizeType.Percent, 100));

            // 컨트롤들을 메인 패널에 추가
            mainPanel.Controls.Add(_showBackgroundCheckBox, 0, 0);
            mainPanel.Controls.Add(_showBoundariesCheckBox, 0, 1);
            mainPanel.Controls.Add(blackbodyLabel, 0, 2);
            mainPanel.Controls.Add(blackbodyPanel, 0, 3);
            mainPanel.Controls.Add(alphaPanel, 0, 4);
            mainPanel.Controls.Add(buttonPanel, 0, 5);

            this.Controls.Add(mainPanel);
        }

        protected override void OnLoad(EventArgs e)
        {
            base.OnLoad(e);

            // 초기값 설정
            _showBackgroundCheckBox.Checked = ShowBackground;
            _showBoundariesCheckBox.Checked = ShowBoundaries;
            _alphaTrackBar.Value = BackgroundAlpha;
            _alphaLabel.Text = $"{BackgroundAlpha}%";

            // Blackbody 체크박스 초기값 설정
            var intervals = new[] { 100, 500, 1000, 1500 };
            for (int i = 0; i < intervals.Length; i++)
            {
                if (BlackbodyIntervals.ContainsKey(intervals[i]))
                {
                    _blackbodyCheckBoxes[i].Checked = BlackbodyIntervals[intervals[i]];
                }
            }
        }

        private void AlphaTrackBar_ValueChanged(object sender, EventArgs e)
        {
            _alphaLabel.Text = $"{_alphaTrackBar.Value}%";
        }

        private void CloseButton_Click(object sender, EventArgs e)
        {
            // 설정값 저장
            ShowBackground = _showBackgroundCheckBox.Checked;
            ShowBoundaries = _showBoundariesCheckBox.Checked;
            BackgroundAlpha = _alphaTrackBar.Value;

            // Blackbody 설정 저장
            var intervals = new[] { 100, 500, 1000, 1500 };
            BlackbodyIntervals.Clear();
            for (int i = 0; i < intervals.Length; i++)
            {
                BlackbodyIntervals[intervals[i]] = _blackbodyCheckBoxes[i].Checked;
            }

            this.DialogResult = DialogResult.OK;
            this.Close();
        }
    }
}