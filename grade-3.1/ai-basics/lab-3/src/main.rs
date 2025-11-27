use std::f64::consts::PI;
use std::io;

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
            self.buf = input.split_whitespace().rev().map(String::from).collect();
        }
    }
}

// Simple xorshift64 RNG
struct Rng {
    state: u64,
}

impl Rng {
    fn new(seed: u64) -> Self {
        Self {
            state: if seed == 0 { 1 } else { seed },
        }
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
    fn new(x: f64, y: f64) -> Self {
        Self { x, y }
    }
}

struct Movement {
    lidar_measurements: Vec<f64>,
    robot_movement: Option<Coord2D>,
}

impl Movement {
    fn new(lidar_measurements: Vec<f64>, robot_movement: Option<Coord2D>) -> Self {
        Self {
            lidar_measurements,
            robot_movement,
        }
    }

    fn read_from_input(
        scanner: &mut Scanner,
        num_measurements: usize,
        has_movement_coord: bool,
    ) -> Self {
        let mut lidar_measurements = Vec::with_capacity(num_measurements);
        for _ in 0..num_measurements {
            let measurement: f64 = scanner.next();
            lidar_measurements.push(measurement);
        }

        if has_movement_coord {
            let robot_movement = Coord2D::new(scanner.next(), scanner.next());
            Self::new(lidar_measurements, Some(robot_movement))
        } else {
            Self {
                lidar_measurements,
                robot_movement: None,
            }
        }
    }
}

// Check if point is inside polygon using ray casting
fn point_in_polygon(point: &Coord2D, polygon: &[Coord2D]) -> bool {
    let n = polygon.len();
    let mut inside = false;
    let mut j = n - 1;

    for i in 0..n {
        let pi = &polygon[i];
        let pj = &polygon[j];

        if ((pi.y > point.y) != (pj.y > point.y))
            && (point.x < (pj.x - pi.x) * (point.y - pi.y) / (pj.y - pi.y) + pi.x)
        {
            inside = !inside;
        }
        j = i;
    }
    inside
}

// Calculate distance from point to wall in direction given by angle
fn ray_cast(point: &Coord2D, angle: f64, polygon: &[Coord2D]) -> f64 {
    let dx = angle.cos();
    let dy = angle.sin();
    let n = polygon.len();
    let mut min_dist = f64::MAX;

    for i in 0..n {
        let p1 = &polygon[i];
        let p2 = &polygon[(i + 1) % n];

        let edge_dx = p2.x - p1.x;
        let edge_dy = p2.y - p1.y;

        let denom = dx * edge_dy - dy * edge_dx;
        if denom.abs() < 1e-12 {
            continue;
        }

        let t = ((p1.x - point.x) * edge_dy - (p1.y - point.y) * edge_dx) / denom;
        let s = ((p1.x - point.x) * dy - (p1.y - point.y) * dx) / denom;

        if t > 1e-9 && s >= 0.0 && s <= 1.0 {
            min_dist = min_dist.min(t);
        }
    }

    min_dist
}

// Calculate expected lidar measurements from a position
fn expected_measurements(pos: &Coord2D, k: usize, polygon: &[Coord2D]) -> Vec<f64> {
    let angle_step = 2.0 * PI / k as f64;
    (0..k)
        .map(|i| ray_cast(pos, i as f64 * angle_step, polygon))
        .collect()
}

// Calculate log-likelihood of measurements given position
fn measurement_log_likelihood(
    pos: &Coord2D,
    measurements: &[f64],
    sl: f64,
    polygon: &[Coord2D],
) -> f64 {
    let expected = expected_measurements(pos, measurements.len(), polygon);
    let var = sl * sl;
    let mut log_likelihood = 0.0;

    for (m, e) in measurements.iter().zip(expected.iter()) {
        if *e < f64::MAX / 2.0 {
            let diff = m - e;
            log_likelihood -= diff * diff / (2.0 * var);
        }
    }

    log_likelihood
}

// Get bounding box of polygon
fn get_bounding_box(polygon: &[Coord2D]) -> (f64, f64, f64, f64) {
    let min_x = polygon.iter().map(|p| p.x).fold(f64::MAX, f64::min);
    let max_x = polygon.iter().map(|p| p.x).fold(f64::MIN, f64::max);
    let min_y = polygon.iter().map(|p| p.y).fold(f64::MAX, f64::min);
    let max_y = polygon.iter().map(|p| p.y).fold(f64::MIN, f64::max);
    (min_x, max_x, min_y, max_y)
}

// Generate random point inside polygon
fn random_point_in_polygon(polygon: &[Coord2D], rng: &mut Rng) -> Coord2D {
    let (min_x, max_x, min_y, max_y) = get_bounding_box(polygon);

    loop {
        let x = rng.gen_range(min_x, max_x);
        let y = rng.gen_range(min_y, max_y);
        let point = Coord2D::new(x, y);
        if point_in_polygon(&point, polygon) {
            return point;
        }
    }
}

// Run particle filter and return (final_position, total_log_likelihood)
fn run_particle_filter(
    polygon: &[Coord2D],
    movements: &[Movement],
    last_measurement: &Movement,
    start_position: Option<Coord2D>,
    sl: f64,
    sx: f64,
    sy: f64,
    num_particles: usize,
    seed: u64,
) -> (Coord2D, f64) {
    let mut rng = Rng::new(seed);

    // Initialize particles
    let mut particles: Vec<Coord2D> = if let Some(start) = start_position {
        (0..num_particles)
            .map(|_| Coord2D::new(rng.gen_normal(start.x, sx), rng.gen_normal(start.y, sy)))
            .collect()
    } else {
        (0..num_particles)
            .map(|_| random_point_in_polygon(polygon, &mut rng))
            .collect()
    };

    let mut total_log_likelihood = 0.0;

    // Process each movement
    for movement in movements {
        // Calculate log-weights based on lidar measurements
        let log_weights: Vec<f64> = particles
            .iter()
            .map(|p| {
                if point_in_polygon(p, polygon) {
                    measurement_log_likelihood(p, &movement.lidar_measurements, sl, polygon)
                } else {
                    f64::NEG_INFINITY
                }
            })
            .collect();

        // Find max log-weight for numerical stability
        let max_log_weight = log_weights
            .iter()
            .cloned()
            .fold(f64::NEG_INFINITY, f64::max);

        // Convert to weights
        let mut weights: Vec<f64> = log_weights
            .iter()
            .map(|lw| (*lw - max_log_weight).exp())
            .collect();

        // Normalize weights
        let weight_sum: f64 = weights.iter().sum();
        total_log_likelihood += max_log_weight + weight_sum.ln() - (num_particles as f64).ln();

        if weight_sum > 1e-300 {
            for w in &mut weights {
                *w /= weight_sum;
            }
        } else {
            let uniform = 1.0 / num_particles as f64;
            for w in &mut weights {
                *w = uniform;
            }
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

        // Apply movement with noise
        if let Some(mov) = &movement.robot_movement {
            for p in &mut new_particles {
                p.x += mov.x + rng.gen_normal(0.0, sx);
                p.y += mov.y + rng.gen_normal(0.0, sy);
            }
        }

        particles = new_particles;
    }

    // Final update with last measurement
    let log_weights: Vec<f64> = particles
        .iter()
        .map(|p| {
            if point_in_polygon(p, polygon) {
                measurement_log_likelihood(p, &last_measurement.lidar_measurements, sl, polygon)
            } else {
                f64::NEG_INFINITY
            }
        })
        .collect();

    let max_log_weight = log_weights
        .iter()
        .cloned()
        .fold(f64::NEG_INFINITY, f64::max);

    let mut weights: Vec<f64> = log_weights
        .iter()
        .map(|lw| (*lw - max_log_weight).exp())
        .collect();

    let weight_sum: f64 = weights.iter().sum();
    total_log_likelihood += max_log_weight + weight_sum.ln() - (num_particles as f64).ln();

    if weight_sum > 1e-300 {
        for w in &mut weights {
            *w /= weight_sum;
        }
    } else {
        let uniform = 1.0 / num_particles as f64;
        for w in &mut weights {
            *w = uniform;
        }
    }

    // Calculate weighted mean position
    let mut mean_x = 0.0;
    let mut mean_y = 0.0;
    for (p, w) in particles.iter().zip(weights.iter()) {
        mean_x += p.x * w;
        mean_y += p.y * w;
    }

    (Coord2D::new(mean_x, mean_y), total_log_likelihood)
}

fn main() {
    let mut scanner = Scanner::new();
    let n: usize = scanner.next();

    let polygon: Vec<Coord2D> = (0..n)
        .map(|_| Coord2D::new(scanner.next(), scanner.next()))
        .collect();

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

    let movements: Vec<Movement> = (0..movements_count)
        .map(|_| Movement::read_from_input(&mut scanner, k, true))
        .collect();
    let last_measurement = Movement::read_from_input(&mut scanner, k, false);

    let base_particles = 1000;
    let num_runs = 1;

    let mut best_result = Coord2D::new(0.0, 0.0);
    let mut best_log_likelihood = f64::NEG_INFINITY;

    for run in 0..num_runs {
        let (result, log_likelihood) = run_particle_filter(
            &polygon,
            &movements,
            &last_measurement,
            start_position,
            sl,
            sx,
            sy,
            base_particles,
            run as u64 * 12345 + 42,
        );

        if log_likelihood > best_log_likelihood {
            best_log_likelihood = log_likelihood;
            best_result = result;
        }
    }

    println!("{} {}", best_result.x, best_result.y);
}
