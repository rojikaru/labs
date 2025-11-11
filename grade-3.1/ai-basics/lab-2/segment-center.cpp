#include <bits/stdc++.h>
using namespace std;

using segment = tuple<double, double, double, double, double, double>;

constexpr int MAX_ITERATIONS = 1'000;

double distance_point_segment(double px, double py, double pz,
                              double ax, double ay, double az,
                              double bx, double by, double bz)
{
    // AB vector
    double abx = bx - ax, aby = by - ay, abz = bz - az;

    // AP vector
    double apx = px - ax, apy = py - ay, apz = pz - az;

    // Project point P onto line AB, computing parameterized position t
    double ab2 = abx * abx + aby * aby + abz * abz;
    double t = (ab2 != 0) ? (apx * abx + apy * aby + apz * abz) / ab2 : 0.0;
    t = clamp(t, 0.0, 1.0);

    // Find the closest point on the segment
    double closest_x = ax + abx * t;
    double closest_y = ay + aby * t;
    double closest_z = az + abz * t;

    // Distance from P to the closest point
    double dx = px - closest_x;
    double dy = py - closest_y;
    double dz = pz - closest_z;

    // Return the Euclidean distance
    return sqrt(dx * dx + dy * dy + dz * dz);
}

double total_distance(double px, double py, double pz, const vector<segment> &segments)
{
    double total = 0.0;
    for (const auto &[ax, ay, az, bx, by, bz] : segments)
    {
        total += distance_point_segment(px, py, pz, ax, ay, az, bx, by, bz);
    }
    return total;
}

int main()
{
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<segment> segments(n);
    for (auto &[ax, ay, az, bx, by, bz] : segments)
    {
        cin >> ax >> ay >> az >> bx >> by >> bz;
    }

    double px = 0.0, py = 0.0, pz = 0.0;
    for (const auto &[ax, ay, az, bx, by, bz] : segments)
    {
        px += (ax + bx) / 2.0;
        py += (ay + by) / 2.0;
        pz += (az + bz) / 2.0;
    }
    px /= n;
    py /= n;
    pz /= n;

    double best_dist = total_distance(px, py, pz, segments);
    auto best_point = tuple{px, py, pz};
    double step = 1.0;

    for (int iter = 0; iter < MAX_ITERATIONS; ++iter)
    {
        bool improved = false;
        for (int dx = -1; dx <= 1; ++dx)
            for (int dy = -1; dy <= 1; ++dy)
                for (int dz = -1; dz <= 1; ++dz)
                {
                    if (dx == 0 && dy == 0 && dz == 0)
                        continue;

                    double nx = px + dx * step;
                    double ny = py + dy * step;
                    double nz = pz + dz * step;
                    double dist = total_distance(nx, ny, nz, segments);
                    if (dist < best_dist)
                    {
                        best_dist = dist;
                        best_point = tuple{nx, ny, nz};
                        improved = true;
                    }
                }

        if (improved) tie(px, py, pz) = best_point;
        else step *= 0.5;
    }

    cout << best_dist << "\n";

    return 0;
}
