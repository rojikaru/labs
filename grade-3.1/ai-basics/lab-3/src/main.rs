use std::f64::consts::PI;
use std::io;

const NUM_PARTICLES: usize = 110;
const RANDOM_SEED: u64 = 42;
const RESAMPLE_THRESHOLD: f64 = 0.5; // Resample when N_eff < threshold * N

struct Scanner {
    buf: Vec<String>,
}

impl Scanner {
    fn new() -> Self {
        Self { buf: Vec::new() }
    }

    fn next<T: std::str::FromStr>(&mut self) -> T {
        loop {
            if let Some(token) = self.buf.pop() {
                return token.parse().ok().unwrap();
            }
            let mut input = String::new();
            io::stdin().read_line(&mut input).unwrap();
            self.buf =
                input.split_whitespace().rev().map(String::from).collect();
        }
    }
}

// Simple xorshift64 RNG
struct Rng {
    state: u64,
}

impl Rng {
    fn new(seed: u64) -> Self {
        Self { state: if seed == 0 { 1 } else { seed } }
    }

    fn next_u64(&mut self) -> u64 {
        let mut x = self.state;
        x ^= x << 13;
        x ^= x >> 7;
        x ^= x << 17;
        self.state = x;
        x
    }

    // Generate uniform random f64 in [0, 1)
    fn next_f64(&mut self) -> f64 {
        (self.next_u64() >> 11) as f64 / (1u64 << 53) as f64
    }

    // Generate uniform random f64 in [low, high)
    fn gen_range(&mut self, low: f64, high: f64) -> f64 {
        low + self.next_f64() * (high - low)
    }

    // Generate normal distribution using Box-Muller transform
    fn gen_normal(&mut self, mean: f64, std_dev: f64) -> f64 {
        let u1 = self.next_f64().max(1e-15); // Avoid log(0)
        let u2 = self.next_f64();
        let z = (-2.0 * u1.ln()).sqrt() * (2.0 * PI * u2).cos();
        mean + z * std_dev
    }
}

#[derive(Clone, Copy)]
struct Coord2D {
    x: f64,
    y: f64,
}

impl Coord2D {
    #[inline(always)]
    fn new(x: f64, y: f64) -> Self {
        Self { x, y }
    }
}

// Precomputed edge data for faster ray casting
#[derive(Clone, Copy)]
struct Edge {
    p1: Coord2D,
    dx: f64,
    dy: f64,
}

struct BoundingBox {
    min_x: f64,
    max_x: f64,
    min_y: f64,
    max_y: f64,
}

impl BoundingBox {
    #[inline(always)]
    fn new(min_x: f64, max_x: f64, min_y: f64, max_y: f64) -> Self {
        Self { min_x, max_x, min_y, max_y }
    }

    #[inline(always)]
    fn contains(&self, point: Coord2D) -> bool {
        point.x >= self.min_x
            && point.x <= self.max_x
            && point.y >= self.min_y
            && point.y <= self.max_y
    }

    #[inline(always)]
    fn from_points(points: &[Coord2D]) -> Self {
        let (min_x, max_x, min_y, max_y) = points.iter().fold(
            (f64::MAX, f64::MIN, f64::MAX, f64::MIN),
            |(min_x, max_x, min_y, max_y), p| {
                (
                    min_x.min(p.x),
                    max_x.max(p.x),
                    min_y.min(p.y),
                    max_y.max(p.y),
                )
            },
        );
        Self::new(min_x, max_x, min_y, max_y)
    }
}

// Cached polygon data for optimized geometric operations
struct Polygon {
    vertices: Vec<Coord2D>,
    edges: Vec<Edge>,
    bbox: BoundingBox,
}

impl Polygon {
    #[inline(always)]
    fn new(polygon: Vec<Coord2D>) -> Self {
        let n = polygon.len();
        let edges: Vec<Edge> = (0..n)
            .map(|i| {
                let p1 = polygon[i];
                let p2 = polygon[(i + 1) % n];
                Edge { p1, dx: p2.x - p1.x, dy: p2.y - p1.y }
            })
            .collect();
        let bbox = BoundingBox::from_points(&polygon);
        Self { vertices: polygon, edges, bbox }
    }

    // Check if point is inside polygon using ray casting (with bbox optimization)
    #[inline]
    fn contains_point(&self, point: Coord2D) -> bool {
        // Quick rejection using bounding box
        if !self.bbox.contains(point) {
            return false;
        }

        let polygon = &self.vertices;
        let n = polygon.len();
        let mut inside = false;
        let mut j = n - 1;

        for i in 0..n {
            let pi = &polygon[i];
            let pj = &polygon[j];

            if ((pi.y > point.y) != (pj.y > point.y))
                && (point.x
                    < (pj.x - pi.x) * (point.y - pi.y) / (pj.y - pi.y) + pi.x)
            {
                inside = !inside;
            }
            j = i;
        }
        inside
    }

    fn random_point_inside(&self, rng: &mut Rng) -> Coord2D {
        loop {
            let x = rng.gen_range(self.bbox.min_x, self.bbox.max_x);
            let y = rng.gen_range(self.bbox.min_y, self.bbox.max_y);
            let point = Coord2D::new(x, y);
            if self.contains_point(point) {
                return point;
            }
        }
    }
}

struct Movement {
    lidar_measurements: Vec<f64>,
    robot_movement: Option<Coord2D>,
}

impl Movement {
    fn new(
        lidar_measurements: Vec<f64>,
        robot_movement: Option<Coord2D>,
    ) -> Self {
        Self { lidar_measurements, robot_movement }
    }

    fn read_from_input(
        scanner: &mut Scanner,
        num_measurements: usize,
        has_movement_coord: bool,
    ) -> Self {
        let lidar_measurements: Vec<f64> =
            (0..num_measurements).map(|_| scanner.next()).collect();

        if !has_movement_coord {
            return Self::new(lidar_measurements, None);
        }

        let robot_movement = Coord2D::new(scanner.next(), scanner.next());
        Self::new(lidar_measurements, Some(robot_movement))
    }
}

// Calculate distance from point to wall in direction given by angle (using cached edges)
#[inline]
fn ray_cast(polygon: &Polygon, point: Coord2D, angle: f64) -> f64 {
    let dx = angle.cos();
    let dy = angle.sin();

    polygon.edges.iter().fold(f64::MAX, |min_dist, edge| {
        let denom = dx * edge.dy - dy * edge.dx;
        if denom.abs() < 1e-12 {
            return min_dist;
        }

        let diff_x = edge.p1.x - point.x;
        let diff_y = edge.p1.y - point.y;

        let t = (diff_x * edge.dy - diff_y * edge.dx) / denom;
        let s = (diff_x * dy - diff_y * dx) / denom;

        if t > 1e-9 && s >= 0.0 && s <= 1.0 {
            min_dist.min(t)
        } else {
            min_dist
        }
    })
}

// Calculate log-likelihood of measurements given position
#[inline]
fn measurement_log_likelihood(
    polygon: &Polygon,
    pos: Coord2D,
    measurements: &[f64],
    sl: f64,
) -> f64 {
    if !polygon.contains_point(pos) {
        return f64::NEG_INFINITY;
    }

    let k = measurements.len();
    let angle_step = 2.0 * PI / k as f64;
    let expected: Vec<f64> = (0..k)
        .map(|i| ray_cast(polygon, pos, i as f64 * angle_step))
        .collect();
    let inv_2var = 0.5 / sl.powi(2);

    measurements
        .iter()
        .zip(expected.iter())
        .filter_map(|(m, e)| {
            if *e < f64::MAX / 2.0 {
                Some(-(m - e).powi(2) * inv_2var)
            } else {
                None
            }
        })
        .sum()
}

// Check if resampling is needed based on effective sample size
#[inline]
fn needs_resampling(weights: &[f64], threshold: f64) -> bool {
    let weight_sum_sq: f64 = weights.iter().map(|w| w.powi(2)).sum();
    let effective_sample_size =
        if weight_sum_sq > 1e-300 { 1.0 / weight_sum_sq } else { 0.0 };
    effective_sample_size < threshold * weights.len() as f64
}

#[inline]
fn resample(
    weights: &[f64],
    resample_threshold: f64,
    particles: &Vec<Coord2D>,
    num_particles: usize,
    rng: &mut Rng,
) -> Option<Vec<Coord2D>> {
    // Only resample when effective sample size drops below threshold
    if !needs_resampling(&weights, resample_threshold) {
        return None;
    }

    // Resample particles using systematic resampling
    let mut new_particles = Vec::with_capacity(num_particles);
    let step = 1.0 / num_particles as f64;
    let mut r = rng.gen_range(0.0, step);
    let mut cumulative = weights[0];
    let mut j = 0;

    for _ in 0..num_particles {
        while cumulative < r && j < num_particles - 1 {
            j += 1;
            cumulative += weights[j];
        }
        new_particles.push(particles[j]);
        r += step;
    }

    Some(new_particles)
}

fn calc_weights(
    polygon: &Polygon,
    particles: &Vec<Coord2D>,
    measurements: &[f64],
    sl: f64,
) -> Vec<f64> {
    let log_weights: Vec<f64> = particles
        .iter()
        .map(|point| {
            measurement_log_likelihood(polygon, *point, measurements, sl)
        })
        .collect();

    let max_log_weight = log_weights
        .iter()
        .cloned()
        .fold(f64::NEG_INFINITY, f64::max);

    let weights: Vec<f64> = log_weights
        .iter()
        .map(|lw| (*lw - max_log_weight).exp())
        .collect();
    let weight_sum: f64 = weights.iter().sum();

    weights
        .iter()
        .map(|w| {
            if weight_sum > 1e-300 {
                *w / weight_sum
            } else {
                1.0 / particles.len() as f64
            }
        })
        .collect()
}

fn run_particle_filter(
    polygon: &Polygon,
    movements: &[Movement],
    start_position: Option<Coord2D>,
    sl: f64,
    sx: f64,
    sy: f64,
    num_particles: usize,
    random_seed: u64,
    resample_threshold: f64,
) -> Coord2D {
    let mut rng = Rng::new(random_seed);
    let mut particles: Vec<Coord2D> = if let Some(start_pos) = start_position {
        (0..num_particles)
            .map(|_| {
                Coord2D::new(
                    rng.gen_normal(start_pos.x, sx),
                    rng.gen_normal(start_pos.y, sy),
                )
            })
            .collect()
    } else {
        (0..num_particles)
            .map(|_| polygon.random_point_inside(&mut rng))
            .collect()
    };
    let mut weights: Vec<f64> = vec![];

    for movement in movements {
        weights =
            calc_weights(polygon, &particles, &movement.lidar_measurements, sl);

        particles = match resample(
            &weights,
            resample_threshold,
            &particles,
            num_particles,
            &mut rng,
        ) {
            Some(new_particles) => new_particles,
            None => particles,
        };

        // Apply movement with noise
        if let Some(mov) = &movement.robot_movement {
            for p in &mut particles {
                p.x += mov.x + rng.gen_normal(0.0, sx);
                p.y += mov.y + rng.gen_normal(0.0, sy);
            }
        }
    }

    // Calculate weighted mean position
    let (mean_x, mean_y) = particles
        .iter()
        .zip(weights.iter())
        .fold((0.0, 0.0), |(mx, my), (p, w)| (mx + p.x * w, my + p.y * w));

    Coord2D::new(mean_x, mean_y)
}

fn main() {
    let mut scanner = Scanner::new();
    let n: usize = scanner.next();

    let polygon: Vec<Coord2D> = (0..n)
        .map(|_| Coord2D::new(scanner.next(), scanner.next()))
        .collect();

    let polygon = Polygon::new(polygon);

    let movements_count: usize = scanner.next();
    let k: usize = scanner.next();

    let sl: f64 = scanner.next();
    let sx: f64 = scanner.next();
    let sy: f64 = scanner.next();

    let start_position = if scanner.next::<u8>() != 0 {
        Some(Coord2D::new(scanner.next(), scanner.next()))
    } else {
        None
    };

    let mut movements: Vec<Movement> = (0..movements_count)
        .map(|_| Movement::read_from_input(&mut scanner, k, true))
        .collect();
    let last_measurement = Movement::read_from_input(&mut scanner, k, false);
    movements.push(last_measurement);

    // Concat last measurement to movements

    let final_position = run_particle_filter(
        &polygon,
        &movements,
        start_position,
        sl,
        sx,
        sy,
        NUM_PARTICLES,
        RANDOM_SEED,
        RESAMPLE_THRESHOLD,
    );

    println!("{} {}", final_position.x, final_position.y);
}
