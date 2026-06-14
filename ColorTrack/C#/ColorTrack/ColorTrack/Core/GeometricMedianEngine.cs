using System;
using System.Collections.Generic;
using System.Linq;

namespace ColorTrack.Core
{
    /// <summary>
    /// 기하 중앙값(Geometric Median) 계산 엔진 - Weiszfeld 알고리즘 구현
    /// </summary>
    public static class GeometricMedianEngine
    {
        /// <summary>
        /// 2D 점들의 기하 중앙값 계산
        /// </summary>
        /// <param name="points">2D 점들의 리스트 (x, y)</param>
        /// <param name="tolerance">수렴 허용 오차</param>
        /// <param name="maxIterations">최대 반복 횟수</param>
        /// <returns>기하 중앙값 (x, y)</returns>
        public static (double x, double y) Calculate(IEnumerable<(double x, double y)> points,
            double tolerance = 1e-5, int maxIterations = 100)
        {
            var pointArray = points.ToArray();
            if (pointArray.Length == 0)
                throw new ArgumentException("Points collection cannot be empty");

            if (pointArray.Length == 1)
                return pointArray[0];

            // 초기값을 일반적인 중앙값으로 설정
            var median = CalculateMedian(pointArray);

            for (int iteration = 0; iteration < maxIterations; iteration++)
            {
                var weights = new double[pointArray.Length];
                var totalWeight = 0.0;
                var hasZeroDistance = false;

                // 각 점까지의 거리 계산 및 가중치 설정
                for (int i = 0; i < pointArray.Length; i++)
                {
                    var distance = CalculateDistance(median, pointArray[i]);

                    if (distance == 0)
                    {
                        // 현재 median이 점들 중 하나와 정확히 일치하는 경우
                        hasZeroDistance = true;
                        break;
                    }

                    weights[i] = 1.0 / distance;
                    totalWeight += weights[i];
                }

                if (hasZeroDistance)
                {
                    // 이미 최적해에 도달
                    return median;
                }

                // 가중 평균으로 다음 median 계산
                var nextMedian = CalculateWeightedAverage(pointArray, weights, totalWeight);

                // 수렴 확인
                var convergenceDistance = CalculateDistance(nextMedian, median);
                if (convergenceDistance < tolerance)
                {
                    return nextMedian;
                }

                median = nextMedian;
            }

            return median;
        }

        /// <summary>
        /// 일반적인 중앙값 계산 (각 차원별로)
        /// </summary>
        private static (double x, double y) CalculateMedian((double x, double y)[] points)
        {
            var xValues = points.Select(p => p.x).OrderBy(x => x).ToArray();
            var yValues = points.Select(p => p.y).OrderBy(y => y).ToArray();

            var medianX = CalculateMedianValue(xValues);
            var medianY = CalculateMedianValue(yValues);

            return (medianX, medianY);
        }

        /// <summary>
        /// 1차원 배열의 중앙값 계산
        /// </summary>
        private static double CalculateMedianValue(double[] values)
        {
            int n = values.Length;
            if (n % 2 == 0)
            {
                return (values[n / 2 - 1] + values[n / 2]) / 2.0;
            }
            else
            {
                return values[n / 2];
            }
        }

        /// <summary>
        /// 두 점 간의 유클리드 거리 계산
        /// </summary>
        private static double CalculateDistance((double x, double y) point1, (double x, double y) point2)
        {
            var dx = point1.x - point2.x;
            var dy = point1.y - point2.y;
            return Math.Sqrt(dx * dx + dy * dy);
        }

        /// <summary>
        /// 가중 평균 계산
        /// </summary>
        private static (double x, double y) CalculateWeightedAverage(
            (double x, double y)[] points, double[] weights, double totalWeight)
        {
            var sumX = 0.0;
            var sumY = 0.0;

            for (int i = 0; i < points.Length; i++)
            {
                var normalizedWeight = weights[i] / totalWeight;
                sumX += points[i].x * normalizedWeight;
                sumY += points[i].y * normalizedWeight;
            }

            return (sumX, sumY);
        }

        /// <summary>
        /// 기하 중앙값과 모든 점들 간의 총 거리 계산
        /// </summary>
        public static double CalculateTotalDistance((double x, double y) median,
            IEnumerable<(double x, double y)> points)
        {
            return points.Sum(point => CalculateDistance(median, point));
        }
    }
}