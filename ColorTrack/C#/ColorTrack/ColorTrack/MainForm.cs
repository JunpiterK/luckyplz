using System;
using System.Collections.Generic;
using System.Data;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Windows.Forms;
using ColorTrack.Core;
using OxyPlot;
using OxyPlot.Annotations;
using OxyPlot.Axes;
using OxyPlot.Series;
using OxyPlot.WindowsForms;

namespace ColorTrack
{
    public partial class MainForm : Form
    {
        private DataTable _csvData;
        private readonly int[] _angles = { 0, 15, 30, 45, 60 };
        private readonly Color[] _colors = { Color.Blue, Color.Green, Color.Red, Color.Purple, Color.Orange };
        private readonly Color[] _transitionColors = { Color.DarkOrange, Color.DarkRed, Color.DarkGreen, Color.DarkBlue, Color.DarkViolet };

        // UI 컨트롤들
        private PlotView _plotView1931;
        private PlotView _plotView1976;
        private CheckBox[] _angleCheckBoxes;
        private CheckBox[] _blackbodyCheckBoxes;
        private CheckBox _showBackgroundCheckBox;
        private CheckBox _showBoundariesCheckBox;
        private TrackBar _alphaTrackBar;
        private Label _alphaLabel;
        private Button _loadButton;
        private Button _saveButton;
        private Button _settingsButton;

        // 플롯 모델들
        private PlotModel _plotModel1931;
        private PlotModel _plotModel1976;

        // 설정 값들
        private bool _showBackground = true;
        private bool _showBoundaries = true;
        private int _backgroundAlpha = 70;
        private Dictionary<int, bool> _blackbodyIntervals = new Dictionary<int, bool>
        {
            { 100, false }, { 500, false }, { 1000, false }, { 1500, false }
        };

        // 배경 이미지
        private DataTable? _csvData;
        private Image? _cie1931Background;
        private Image? _cie1976Background;

        // 마우스 좌표 표시용
        private TextAnnotation _coord1931Annotation;
        private TextAnnotation _coord1976Annotation;

        public MainForm()
        {
            InitializeComponent();
            LoadBackgroundImages();
            SetupPlots();
            UpdatePlots();
        }

        private void InitializeComponent()
        {
            this.Text = "ColorTrack - VACS Analyzer";
            this.Size = new Size(1400, 750);
            this.StartPosition = FormStartPosition.CenterScreen;

            // 메인 패널 설정
            var mainPanel = new TableLayoutPanel
            {
                Dock = DockStyle.Fill,
                RowCount = 2,
                ColumnCount = 1
            };
            mainPanel.RowStyles.Add(new RowStyle(SizeType.Absolute, 120)); // 컨트롤 패널
            mainPanel.RowStyles.Add(new RowStyle(SizeType.Percent, 100)); // 플롯 영역

            // 컨트롤 패널 설정
            var controlPanel = CreateControlPanel();
            mainPanel.Controls.Add(controlPanel, 0, 0);

            // 플롯 패널 설정
            var plotPanel = CreatePlotPanel();
            mainPanel.Controls.Add(plotPanel, 0, 1);

            this.Controls.Add(mainPanel);
        }

        private Panel CreateControlPanel()
        {
            var panel = new Panel { Dock = DockStyle.Fill, BackColor = Color.FromArgb(248, 249, 250) };

            // 첫 번째 행 - 버튼들
            var buttonPanel = new FlowLayoutPanel
            {
                Location = new Point(10, 10),
                Size = new Size(1360, 40),
                FlowDirection = FlowDirection.LeftToRight
            };

            _loadButton = new Button
            {
                Text = "📁 Load Data",
                Size = new Size(120, 35),
                BackColor = Color.FromArgb(74, 144, 226),
                ForeColor = Color.White,
                FlatStyle = FlatStyle.Flat,
                Font = new Font("Segoe UI", 10, FontStyle.Bold)
            };
            _loadButton.Click += LoadButton_Click;

            _saveButton = new Button
            {
                Text = "💾 Save Plot",
                Size = new Size(120, 35),
                BackColor = Color.FromArgb(74, 144, 226),
                ForeColor = Color.White,
                FlatStyle = FlatStyle.Flat,
                Font = new Font("Segoe UI", 10, FontStyle.Bold)
            };
            _saveButton.Click += SaveButton_Click;

            _settingsButton = new Button
            {
                Text = "⚙",
                Size = new Size(40, 35),
                BackColor = Color.FromArgb(248, 249, 250),
                ForeColor = Color.FromArgb(108, 117, 125),
                FlatStyle = FlatStyle.Flat,
                Font = new Font("Segoe UI", 12, FontStyle.Bold)
            };
            _settingsButton.Click += SettingsButton_Click;

            buttonPanel.Controls.AddRange(new Control[] { _loadButton, _saveButton, _settingsButton });

            // 두 번째 행 - Viewing Angle 체크박스들
            var anglePanel = new FlowLayoutPanel
            {
                Location = new Point(10, 55),
                Size = new Size(1360, 25),
                FlowDirection = FlowDirection.LeftToRight
            };

            var angleLabel = new Label
            {
                Text = "📐 Viewing Angle:",
                Font = new Font("Segoe UI", 11, FontStyle.Bold),
                ForeColor = Color.FromArgb(73, 80, 87),
                AutoSize = true,
                Margin = new Padding(0, 5, 15, 0)
            };
            anglePanel.Controls.Add(angleLabel);

            _angleCheckBoxes = new CheckBox[_angles.Length];
            for (int i = 0; i < _angles.Length; i++)
            {
                _angleCheckBoxes[i] = new CheckBox
                {
                    Text = $"{_angles[i]}°",
                    Font = new Font("Segoe UI", 10),
                    AutoSize = true,
                    Margin = new Padding(10, 5, 10, 0)
                };
                int angle = _angles[i]; // 클로저 문제 해결
                _angleCheckBoxes[i].CheckedChanged += (s, e) => ToggleAngle(angle, ((CheckBox)s).Checked);
                anglePanel.Controls.Add(_angleCheckBoxes[i]);
            }

            // 세 번째 행 - Blackbody Locus 체크박스들
            var blackbodyPanel = new FlowLayoutPanel
            {
                Location = new Point(10, 85),
                Size = new Size(1360, 25),
                FlowDirection = FlowDirection.LeftToRight
            };

            var blackbodyLabel = new Label
            {
                Text = "🌡️ Blackbody Locus:",
                Font = new Font("Segoe UI", 11, FontStyle.Bold),
                ForeColor = Color.FromArgb(73, 80, 87),
                AutoSize = true,
                Margin = new Padding(0, 5, 15, 0)
            };
            blackbodyPanel.Controls.Add(blackbodyLabel);

            var intervals = new[] { 100, 500, 1000, 1500 };
            _blackbodyCheckBoxes = new CheckBox[intervals.Length];
            for (int i = 0; i < intervals.Length; i++)
            {
                _blackbodyCheckBoxes[i] = new CheckBox
                {
                    Text = $"{intervals[i]}K",
                    Font = new Font("Segoe UI", 10),
                    AutoSize = true,
                    Margin = new Padding(10, 5, 10, 0)
                };
                int interval = intervals[i]; // 클로저 문제 해결
                _blackbodyCheckBoxes[i].CheckedChanged += (s, e) => ToggleBlackbodyInterval(interval, ((CheckBox)s).Checked);
                blackbodyPanel.Controls.Add(_blackbodyCheckBoxes[i]);
            }

            panel.Controls.AddRange(new Control[] { buttonPanel, anglePanel, blackbodyPanel });
            return panel;
        }

        private Panel CreatePlotPanel()
        {
            var panel = new TableLayoutPanel
            {
                Dock = DockStyle.Fill,
                ColumnCount = 2,
                RowCount = 1
            };
            panel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50));
            panel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50));

            // CIE 1931 플롯
            _plotView1931 = new PlotView { Dock = DockStyle.Fill };
            _plotModel1931 = new PlotModel { Title = "CIE 1931" };
            _plotView1931.Model = _plotModel1931;

            // CIE 1976 플롯
            _plotView1976 = new PlotView { Dock = DockStyle.Fill };
            _plotModel1976 = new PlotModel { Title = "CIE 1976" };
            _plotView1976.Model = _plotModel1976;

            // 마우스 이벤트 연결
            _plotView1931.MouseMove += PlotView1931_MouseMove;
            _plotView1976.MouseMove += PlotView1976_MouseMove;

            panel.Controls.Add(_plotView1931, 0, 0);
            panel.Controls.Add(_plotView1976, 1, 0);

            return panel;
        }

        private void LoadBackgroundImages()
        {
            _cie1931Background = BackgroundImageLoader.LoadCie1931Background();
            _cie1976Background = BackgroundImageLoader.LoadCie1976Background();
        }

        private void SetupPlots()
        {
            // CIE 1931 설정
            _plotModel1931.Axes.Clear();
            _plotModel1931.Axes.Add(new LinearAxis
            {
                Position = AxisPosition.Bottom,
                Title = "CIE x",
                Minimum = 0,
                Maximum = 0.8
            });
            _plotModel1931.Axes.Add(new LinearAxis
            {
                Position = AxisPosition.Left,
                Title = "CIE y",
                Minimum = 0,
                Maximum = 0.9
            });

            // CIE 1976 설정
            _plotModel1976.Axes.Clear();
            _plotModel1976.Axes.Add(new LinearAxis
            {
                Position = AxisPosition.Bottom,
                Title = "CIE u'",
                Minimum = 0,
                Maximum = 0.7
            });
            _plotModel1976.Axes.Add(new LinearAxis
            {
                Position = AxisPosition.Left,
                Title = "CIE v'",
                Minimum = 0,
                Maximum = 0.6
            });

            // 좌표 표시용 텍스트 애노테이션 초기화
            _coord1931Annotation = new TextAnnotation
            {
                Text = "",
                TextPosition = new DataPoint(0.02, 0.02),
                FontSize = 8,
                Background = OxyColors.White,
                Stroke = OxyColors.Gray,
                StrokeThickness = 0.5,
                Padding = new OxyThickness(4),
                TextHorizontalAlignment = OxyPlot.HorizontalAlignment.Left,
                TextVerticalAlignment = OxyPlot.VerticalAlignment.Bottom
            };

            _coord1976Annotation = new TextAnnotation
            {
                Text = "",
                TextPosition = new DataPoint(0.02, 0.02),
                FontSize = 8,
                Background = OxyColors.White,
                Stroke = OxyColors.Gray,
                StrokeThickness = 0.5,
                Padding = new OxyThickness(4),
                TextHorizontalAlignment = HorizontalAlignment.Left,
                TextVerticalAlignment = VerticalAlignment.Bottom
            };
        }

        private void PlotView1931_MouseMove(object sender, MouseEventArgs e)
        {
            var plotView = sender as PlotView;
            var screenPoint = new ScreenPoint(e.X, e.Y);

            try
            {
                var dataPoint = plotView.Model.Axes[0].InverseTransform(screenPoint.X, screenPoint.Y, plotView.Model.Axes[1]);

                if (dataPoint.X >= 0 && dataPoint.X <= 0.8 && dataPoint.Y >= 0 && dataPoint.Y <= 0.9)
                {
                    _coord1931Annotation.Text = $"x: {dataPoint.X:F4}\ny: {dataPoint.Y:F4}";

                    // 기존 좌표 애노테이션 제거
                    _plotModel1931.Annotations.Remove(_coord1931Annotation);
                    _plotModel1931.Annotations.Add(_coord1931Annotation);
                    _plotModel1931.InvalidatePlot(false);
                }
            }
            catch
            {
                // 좌표 변환 실패 시 무시
            }
        }

        private void PlotView1976_MouseMove(object sender, MouseEventArgs e)
        {
            var plotView = sender as PlotView;
            var screenPoint = new ScreenPoint(e.X, e.Y);

            try
            {
                var dataPoint = plotView.Model.Axes[0].InverseTransform(screenPoint.X, screenPoint.Y, plotView.Model.Axes[1]);

                if (dataPoint.X >= 0 && dataPoint.X <= 0.7 && dataPoint.Y >= 0 && dataPoint.Y <= 0.6)
                {
                    _coord1976Annotation.Text = $"u': {dataPoint.X:F4}\nv': {dataPoint.Y:F4}";

                    // 기존 좌표 애노테이션 제거
                    _plotModel1976.Annotations.Remove(_coord1976Annotation);
                    _plotModel1976.Annotations.Add(_coord1976Annotation);
                    _plotModel1976.InvalidatePlot(false);
                }
            }
            catch
            {
                // 좌표 변환 실패 시 무시
            }
        }

        private void UpdatePlots()
        {
            _plotModel1931.Series.Clear();
            _plotModel1976.Series.Clear();
            _plotModel1931.Annotations.Clear();
            _plotModel1976.Annotations.Clear();

            // 배경 및 경계선 추가
            if (_showBoundaries)
            {
                AddSpectralLocus();
            }

            // Blackbody locus 추가
            AddBlackbodyLocus();

            // 데이터 플롯
            if (_csvData != null)
            {
                PlotData();
            }

            // 좌표 표시 애노테이션 추가
            _plotModel1931.Annotations.Add(_coord1931Annotation);
            _plotModel1976.Annotations.Add(_coord1976Annotation);

            _plotModel1931.InvalidatePlot(true);
            _plotModel1976.InvalidatePlot(true);
        }

        private void AddSpectralLocus()
        {
            var (spectralX, spectralY) = CieStandardData.CalculateSpectralLocus();

            if (spectralX.Length > 0)
            {
                // CIE 1931 스펙트럼 궤적
                var series1931 = new LineSeries
                {
                    Color = OxyColors.Black,
                    StrokeThickness = 1.5
                };

                for (int i = 0; i < spectralX.Length; i++)
                {
                    series1931.Points.Add(new DataPoint(spectralX[i], spectralY[i]));
                }
                // 궤적을 닫기 위한 선
                series1931.Points.Add(new DataPoint(spectralX[0], spectralY[0]));
                _plotModel1931.Series.Add(series1931);

                // CIE 1976 스펙트럼 궤적
                var series1976 = new LineSeries
                {
                    Color = OxyColors.Black,
                    StrokeThickness = 1.5
                };

                for (int i = 0; i < spectralX.Length; i++)
                {
                    var (u, v) = ColorConversionEngine.XyToUv(spectralX[i], spectralY[i]);
                    if (!double.IsNaN(u) && !double.IsNaN(v))
                    {
                        series1976.Points.Add(new DataPoint(u, v));
                    }
                }
                // 궤적을 닫기 위한 선
                if (series1976.Points.Count > 0)
                {
                    series1976.Points.Add(series1976.Points[0]);
                    _plotModel1976.Series.Add(series1976);
                }
            }
        }

        private void AddBlackbodyLocus()
        {
            var selectedIntervals = _blackbodyIntervals.Where(kv => kv.Value).Select(kv => kv.Key).ToList();

            if (selectedIntervals.Count > 0)
            {
                var blackbodyData = BlackbodyEngine.CalculateBlackbodyLocus();

                if (blackbodyData.X.Length > 0)
                {
                    // CIE 1931 blackbody locus
                    var bbSeries1931 = new LineSeries
                    {
                        Color = OxyColors.Black,
                        StrokeThickness = 2.0
                    };

                    for (int i = 0; i < blackbodyData.X.Length; i++)
                    {
                        bbSeries1931.Points.Add(new DataPoint(blackbodyData.X[i], blackbodyData.Y[i]));
                    }
                    _plotModel1931.Series.Add(bbSeries1931);

                    // CIE 1976 blackbody locus
                    var bbSeries1976 = new LineSeries
                    {
                        Color = OxyColors.Black,
                        StrokeThickness = 2.0
                    };

                    for (int i = 0; i < blackbodyData.U.Length; i++)
                    {
                        bbSeries1976.Points.Add(new DataPoint(blackbodyData.U[i], blackbodyData.V[i]));
                    }
                    _plotModel1976.Series.Add(bbSeries1976);

                    // DUV 라인 추가
                    foreach (var interval in selectedIntervals)
                    {
                        AddDuvLines(interval);
                    }
                }
            }
        }

        private void AddDuvLines(int interval)
        {
            var xAxis = _plotModel1931.Axes.FirstOrDefault(a => a.Position == AxisPosition.Bottom);
            var yAxis = _plotModel1931.Axes.FirstOrDefault(a => a.Position == AxisPosition.Left);
            var uAxis = _plotModel1976.Axes.FirstOrDefault(a => a.Position == AxisPosition.Bottom);
            var vAxis = _plotModel1976.Axes.FirstOrDefault(a => a.Position == AxisPosition.Left);

            if (xAxis == null || yAxis == null || uAxis == null || vAxis == null) return;

            var xRange = (xAxis.ActualMinimum, xAxis.ActualMaximum);
            var yRange = (yAxis.ActualMinimum, yAxis.ActualMaximum);
            var uRange = (uAxis.ActualMinimum, uAxis.ActualMaximum);
            var vRange = (vAxis.ActualMinimum, vAxis.ActualMaximum);

            var (labelData, duvLines) = BlackbodyEngine.GetDuvLinesForRange(xRange, yRange, uRange, vRange, interval);

            // DUV 라인 그리기
            foreach (var line in duvLines.Lines1931)
            {
                var lineSeries = new LineSeries
                {
                    Color = OxyColors.Gray,
                    StrokeThickness = 1.5
                };
                lineSeries.Points.Add(new DataPoint(line.x1, line.y1));
                lineSeries.Points.Add(new DataPoint(line.x2, line.y2));
                _plotModel1931.Series.Add(lineSeries);
            }

            foreach (var line in duvLines.Lines1976)
            {
                var lineSeries = new LineSeries
                {
                    Color = OxyColors.Gray,
                    StrokeThickness = 1.5
                };
                lineSeries.Points.Add(new DataPoint(line.u1, line.v1));
                lineSeries.Points.Add(new DataPoint(line.u2, line.v2));
                _plotModel1976.Series.Add(lineSeries);
            }

            // 온도 라벨 추가
            foreach (var label in labelData)
            {
                var annotation1931 = new TextAnnotation
                {
                    Text = $"{label.Temperature}K",
                    TextPosition = new DataPoint(label.X, label.Y),
                    FontSize = 8,
                    FontWeight = OxyPlot.FontWeights.Bold,
                    TextColor = OxyColors.Black
                };
                _plotModel1931.Annotations.Add(annotation1931);

                var annotation1976 = new TextAnnotation
                {
                    Text = $"{label.Temperature}K",
                    TextPosition = new DataPoint(label.U, label.V),
                    FontSize = 8,
                    FontWeight = OxyPlot.FontWeights.Bold,
                    TextColor = OxyColors.Black
                };
                _plotModel1976.Annotations.Add(annotation1976);
            }
        }

        private void PlotData()
        {
            var selectedAngles = new List<int>();
            for (int i = 0; i < _angles.Length; i++)
            {
                if (_angleCheckBoxes[i].Checked)
                {
                    selectedAngles.Add(_angles[i]);
                }
            }

            if (selectedAngles.Count == 0) return;

            var medians1931 = new List<(double x, double y)>();
            var medians1976 = new List<(double u, double v)>();

            // 각 각도별 데이터 플롯
            foreach (var angle in selectedAngles)
            {
                var colorIndex = Array.IndexOf(_angles, angle);
                var color = OxyColor.FromArgb(255, _colors[colorIndex].R, _colors[colorIndex].G, _colors[colorIndex].B);

                var xColumnName = $"{angle}_x";
                var yColumnName = $"{angle}_y";

                if (!_csvData.Columns.Contains(xColumnName) || !_csvData.Columns.Contains(yColumnName))
                    continue;

                var points1931 = new List<(double x, double y)>();
                var scatterSeries1931 = new ScatterSeries
                {
                    MarkerType = MarkerType.Circle,
                    MarkerSize = 4,
                    MarkerFill = OxyColor.FromArgb(80, color.R, color.G, color.B),
                    MarkerStroke = color,
                    Title = $"{angle}° data"
                };

                var scatterSeries1976 = new ScatterSeries
                {
                    MarkerType = MarkerType.Circle,
                    MarkerSize = 4,
                    MarkerFill = OxyColor.FromArgb(80, color.R, color.G, color.B),
                    MarkerStroke = color,
                    Title = $"{angle}° data"
                };

                foreach (DataRow row in _csvData.Rows)
                {
                    if (double.TryParse(row[xColumnName]?.ToString(), out double x) &&
                        double.TryParse(row[yColumnName]?.ToString(), out double y))
                    {
                        points1931.Add((x, y));
                        scatterSeries1931.Points.Add(new ScatterPoint(x, y));

                        var (u, v) = ColorConversionEngine.XyToUv(x, y);
                        if (!double.IsNaN(u) && !double.IsNaN(v))
                        {
                            scatterSeries1976.Points.Add(new ScatterPoint(u, v));
                        }
                    }
                }

                _plotModel1931.Series.Add(scatterSeries1931);
                _plotModel1976.Series.Add(scatterSeries1976);

                // 기하 중앙값 계산
                if (points1931.Count > 0)
                {
                    var median1931 = GeometricMedianEngine.Calculate(points1931);
                    var median1976 = ColorConversionEngine.XyToUv(median1931.x, median1931.y);

                    medians1931.Add(median1931);
                    medians1976.Add(median1976);

                    // 중앙값 표시
                    var medianSeries1931 = new ScatterSeries
                    {
                        MarkerType = MarkerType.Circle,
                        MarkerSize = 12,
                        MarkerStroke = color,
                        MarkerStrokeThickness = 3,
                        MarkerFill = OxyColors.Transparent,
                        Title = $"{angle}° median"
                    };
                    medianSeries1931.Points.Add(new ScatterPoint(median1931.x, median1931.y));
                    _plotModel1931.Series.Add(medianSeries1931);

                    if (!double.IsNaN(median1976.u) && !double.IsNaN(median1976.v))
                    {
                        var medianSeries1976 = new ScatterSeries
                        {
                            MarkerType = MarkerType.Circle,
                            MarkerSize = 12,
                            MarkerStroke = color,
                            MarkerStrokeThickness = 3,
                            MarkerFill = OxyColors.Transparent,
                            Title = $"{angle}° median"
                        };
                        medianSeries1976.Points.Add(new ScatterPoint(median1976.u, median1976.v));
                        _plotModel1976.Series.Add(medianSeries1976);
                    }
                }
            }

            // 화살표 및 색차 정보 추가
            AddTransitionArrows(medians1931, medians1976, selectedAngles);
        }

        private void AddTransitionArrows(List<(double x, double y)> medians1931,
            List<(double u, double v)> medians1976, List<int> selectedAngles)
        {
            if (medians1931.Count < 2) return;

            double totalDeltaE = 0;

            for (int i = 0; i < medians1931.Count - 1; i++)
            {
                var color = OxyColor.FromArgb(255, _transitionColors[i % _transitionColors.Length].R,
                    _transitionColors[i % _transitionColors.Length].G, _transitionColors[i % _transitionColors.Length].B);

                // CIE 1931 화살표
                var arrow1931 = new ArrowAnnotation
                {
                    StartPoint = new DataPoint(medians1931[i].x, medians1931[i].y),
                    EndPoint = new DataPoint(medians1931[i + 1].x, medians1931[i + 1].y),
                    Color = color,
                    StrokeThickness = 3,
                    HeadLength = 8,
                    HeadWidth = 4
                };
                _plotModel1931.Annotations.Add(arrow1931);

                // CIE 1976 화살표
                if (!double.IsNaN(medians1976[i].u) && !double.IsNaN(medians1976[i].v) &&
                    !double.IsNaN(medians1976[i + 1].u) && !double.IsNaN(medians1976[i + 1].v))
                {
                    var arrow1976 = new ArrowAnnotation
                    {
                        StartPoint = new DataPoint(medians1976[i].u, medians1976[i].v),
                        EndPoint = new DataPoint(medians1976[i + 1].u, medians1976[i + 1].v),
                        Color = color,
                        StrokeThickness = 3,
                        HeadLength = 8,
                        HeadWidth = 4
                    };
                    _plotModel1976.Annotations.Add(arrow1976);
                }

                // 거리 및 색차 계산
                var d1931 = ColorConversionEngine.CalculateXYDistance(
                    medians1931[i].x, medians1931[i].y, medians1931[i + 1].x, medians1931[i + 1].y);
                var d1976 = ColorConversionEngine.CalculateUVDistance(
                    medians1976[i].u, medians1976[i].v, medians1976[i + 1].u, medians1976[i + 1].v);

                var lab1 = ColorConversionEngine.XyToLab(medians1931[i].x, medians1931[i].y);
                var lab2 = ColorConversionEngine.XyToLab(medians1931[i + 1].x, medians1931[i + 1].y);
                var deltaE = ColorConversionEngine.DeltaE2000(lab1, lab2);
                totalDeltaE += deltaE;
            }

            // 총 색차 정보 표시
            if (selectedAngles.Count >= 3)
            {
                var textAnnotation1931 = new TextAnnotation
                {
                    Text = $"Total ΔE00:\n{totalDeltaE:F2}",
                    TextPosition = new DataPoint(0.4, 0.5),
                    FontSize = 10,
                    FontWeight = OxyPlot.FontWeights.Bold,
                    Background = OxyColors.LightBlue,
                    Stroke = OxyColors.Navy,
                    StrokeThickness = 2,
                    Padding = new OxyThickness(8)
                };
                _plotModel1931.Annotations.Add(textAnnotation1931);

                var textAnnotation1976 = new TextAnnotation
                {
                    Text = $"Total ΔE00:\n{totalDeltaE:F2}",
                    TextPosition = new DataPoint(0.35, 0.3),
                    FontSize = 10,
                    FontWeight = OxyPlot.FontWeights.Bold,
                    Background = OxyColors.LightBlue,
                    Stroke = OxyColors.Navy,
                    StrokeThickness = 2,
                    Padding = new OxyThickness(8)
                };
                _plotModel1976.Annotations.Add(textAnnotation1976);
            }
        }

        private void ToggleAngle(int angle, bool isChecked)
        {
            UpdatePlots();
        }

        private void ToggleBlackbodyInterval(int interval, bool isChecked)
        {
            _blackbodyIntervals[interval] = isChecked;
            UpdatePlots();
        }

        private void LoadButton_Click(object sender, EventArgs e)
        {
            using (var openFileDialog = new OpenFileDialog())
            {
                openFileDialog.Filter = "CSV files (*.csv)|*.csv|All files (*.*)|*.*";
                openFileDialog.Title = "Select CSV File";

                if (openFileDialog.ShowDialog() == DialogResult.OK)
                {
                    try
                    {
                        _csvData = LoadCsvFile(openFileDialog.FileName);

                        // 모든 체크박스 해제
                        foreach (var checkBox in _angleCheckBoxes)
                        {
                            checkBox.Checked = false;
                        }

                        UpdatePlots();
                        this.Text = $"ColorTrack - {Path.GetFileName(openFileDialog.FileName)} ({_csvData.Rows.Count} rows)";
                    }
                    catch (Exception ex)
                    {
                        MessageBox.Show($"Error loading file: {ex.Message}", "Error",
                            MessageBoxButtons.OK, MessageBoxIcon.Error);
                    }
                }
            }
        }

        private DataTable LoadCsvFile(string filePath)
        {
            var dataTable = new DataTable();
            var lines = File.ReadAllLines(filePath);

            if (lines.Length == 0)
                throw new InvalidOperationException("File is empty");

            // 헤더 파싱
            var headers = lines[0].Split(',');
            foreach (var header in headers)
            {
                dataTable.Columns.Add(header.Trim());
            }

            // 데이터 파싱
            for (int i = 1; i < lines.Length; i++)
            {
                var values = lines[i].Split(',');
                if (values.Length == headers.Length)
                {
                    dataTable.Rows.Add(values);
                }
            }

            return dataTable;
        }

        private void SaveButton_Click(object sender, EventArgs e)
        {
            using (var saveFileDialog = new SaveFileDialog())
            {
                saveFileDialog.Filter = "PNG files (*.png)|*.png|All files (*.*)|*.*";
                saveFileDialog.Title = "Save Plot";
                saveFileDialog.FileName = "chromaticity_diagrams.png";

                if (saveFileDialog.ShowDialog() == DialogResult.OK)
                {
                    try
                    {
                        // 두 개의 플롯을 하나의 이미지로 저장
                        SaveCombinedPlots(saveFileDialog.FileName);
                        MessageBox.Show("Plot saved successfully!", "Success",
                            MessageBoxButtons.OK, MessageBoxIcon.Information);
                    }
                    catch (Exception ex)
                    {
                        MessageBox.Show($"Error saving plot: {ex.Message}", "Error",
                            MessageBoxButtons.OK, MessageBoxIcon.Error);
                    }
                }
            }
        }

        private void SaveCombinedPlots(string fileName)
        {
            const int width = 1400;
            const int height = 700;
            const int plotWidth = width / 2;

            using (var bitmap = new Bitmap(width, height))
            using (var graphics = Graphics.FromImage(bitmap))
            {
                graphics.Clear(Color.White);

                // CIE 1931 플롯 저장
                var exporter1931 = new OxyPlot.WindowsForms.PngExporter { Width = plotWidth, Height = height };
                using (var stream1931 = new MemoryStream())
                {
                    exporter1931.Export(_plotModel1931, stream1931);
                    using (var img1931 = Image.FromStream(stream1931))
                    {
                        graphics.DrawImage(img1931, 0, 0, plotWidth, height);
                    }
                }

                // CIE 1976 플롯 저장
                var exporter1976 = new OxyPlot.WindowsForms.PngExporter { Width = plotWidth, Height = height };
                using (var stream1976 = new MemoryStream())
                {
                    exporter1976.Export(_plotModel1976, stream1976);
                    using (var img1976 = Image.FromStream(stream1976))
                    {
                        graphics.DrawImage(img1976, plotWidth, 0, plotWidth, height);
                    }
                }

                bitmap.Save(fileName, System.Drawing.Imaging.ImageFormat.Png);
            }
        }

        private void SettingsButton_Click(object sender, EventArgs e)
        {
            using (var settingsForm = new SettingsForm())
            {
                settingsForm.ShowBackground = _showBackground;
                settingsForm.ShowBoundaries = _showBoundaries;
                settingsForm.BackgroundAlpha = _backgroundAlpha;
                settingsForm.BlackbodyIntervals = new Dictionary<int, bool>(_blackbodyIntervals);

                if (settingsForm.ShowDialog() == DialogResult.OK)
                {
                    _showBackground = settingsForm.ShowBackground;
                    _showBoundaries = settingsForm.ShowBoundaries;
                    _backgroundAlpha = settingsForm.BackgroundAlpha;
                    _blackbodyIntervals = settingsForm.BlackbodyIntervals;

                    // 체크박스 상태 업데이트
                    for (int i = 0; i < _blackbodyCheckBoxes.Length; i++)
                    {
                        var intervals = new[] { 100, 500, 1000, 1500 };
                        _blackbodyCheckBoxes[i].Checked = _blackbodyIntervals[intervals[i]];
                    }

                    UpdatePlots();
                }
            }
        }

        private void AdjustAxisLimitsToData()
        {
            if (_csvData == null) return;

            var selectedAngles = new List<int>();
            for (int i = 0; i < _angles.Length; i++)
            {
                if (_angleCheckBoxes[i].Checked)
                {
                    selectedAngles.Add(_angles[i]);
                }
            }

            if (selectedAngles.Count == 0) return;

            double minX = double.MaxValue, maxX = double.MinValue;
            double minY = double.MaxValue, maxY = double.MinValue;
            double minU = double.MaxValue, maxU = double.MinValue;
            double minV = double.MaxValue, maxV = double.MinValue;

            foreach (var angle in selectedAngles)
            {
                var xColumnName = $"{angle}_x";
                var yColumnName = $"{angle}_y";

                if (!_csvData.Columns.Contains(xColumnName) || !_csvData.Columns.Contains(yColumnName))
                    continue;

                foreach (DataRow row in _csvData.Rows)
                {
                    if (double.TryParse(row[xColumnName]?.ToString(), out double x) &&
                        double.TryParse(row[yColumnName]?.ToString(), out double y))
                    {
                        minX = Math.Min(minX, x); maxX = Math.Max(maxX, x);
                        minY = Math.Min(minY, y); maxY = Math.Max(maxY, y);

                        var (u, v) = ColorConversionEngine.XyToUv(x, y);
                        if (!double.IsNaN(u) && !double.IsNaN(v))
                        {
                            minU = Math.Min(minU, u); maxU = Math.Max(maxU, u);
                            minV = Math.Min(minV, v); maxV = Math.Max(maxV, v);
                        }
                    }
                }
            }

            const double margin = 0.1;
            var xRange = maxX - minX;
            var yRange = maxY - minY;
            var uRange = maxU - minU;
            var vRange = maxV - minV;

            // CIE 1931 축 범위 조정
            _plotModel1931.Axes[0].Minimum = Math.Max(0, minX - xRange * margin);
            _plotModel1931.Axes[0].Maximum = Math.Min(0.8, maxX + xRange * margin);
            _plotModel1931.Axes[1].Minimum = Math.Max(0, minY - yRange * margin);
            _plotModel1931.Axes[1].Maximum = Math.Min(0.9, maxY + yRange * margin);

            // CIE 1976 축 범위 조정
            _plotModel1976.Axes[0].Minimum = Math.Max(0, minU - uRange * margin);
            _plotModel1976.Axes[0].Maximum = Math.Min(0.7, maxU + uRange * margin);
            _plotModel1976.Axes[1].Minimum = Math.Max(0, minV - vRange * margin);
            _plotModel1976.Axes[1].Maximum = Math.Min(0.6, maxV + vRange * margin);
        }

        private void ResetAxisLimits()
        {
            // CIE 1931 기본 범위
            _plotModel1931.Axes[0].Minimum = 0;
            _plotModel1931.Axes[0].Maximum = 0.8;
            _plotModel1931.Axes[1].Minimum = 0;
            _plotModel1931.Axes[1].Maximum = 0.9;

            // CIE 1976 기본 범위
            _plotModel1976.Axes[0].Minimum = 0;
            _plotModel1976.Axes[0].Maximum = 0.7;
            _plotModel1976.Axes[1].Minimum = 0;
            _plotModel1976.Axes[1].Maximum = 0.6;
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing)
            {
                BackgroundImageLoader.DisposeImage(ref _cie1931Background);
                BackgroundImageLoader.DisposeImage(ref _cie1976Background);
            }
            base.Dispose(disposing);
        }
    }
}