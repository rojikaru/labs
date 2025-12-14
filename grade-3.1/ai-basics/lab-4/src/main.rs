pub mod core;
pub mod schema;

use std::{path::Path, time::Instant};

use crate::core::detection::triangles_stats;
use colorize::AnsiColor;
use opencv::imgcodecs;
use schema::test::{Test, TestWithPath};

enum TestStatus {
    Passed,
    Failed,
}

#[inline]
fn run_test(
    index: usize,
    total: usize,
    test: &TestWithPath,
    tests_path: &str,
) -> TestStatus {
    let img = match imgcodecs::imread(
        &format!("{}/{}", tests_path, test.path),
        imgcodecs::IMREAD_COLOR,
    ) {
        Ok(image) => image,
        Err(e) => {
            println!("Failed to read image {}: {}\n", test.path, e);
            return TestStatus::Failed;
        }
    };

    let start_time = Instant::now();
    let detected = match triangles_stats(&img, 8.0) {
        Ok(stats) => stats,
        Err(e) => {
            println!("Failed to process image {}: {}\n", test.path, e);
            return TestStatus::Failed;
        }
    };
    let duration = start_time.elapsed();

    let status = if Test::from(test) == detected {
        TestStatus::Passed
    } else {
        TestStatus::Failed
    };

    println!("Detected: {:?}", detected);
    println!("Expected: {:?}", test);
    println!(
        "Test {}/{}: {}, Duration: {:?}\n",
        index + 1,
        total,
        match status {
            TestStatus::Passed => "PASSED".green(),
            TestStatus::Failed => "FAILED".red(),
        },
        duration
    );

    status
}

#[inline]
fn tests(tests_path: &str) {
    let tests = match TestWithPath::array_from_json_file(&format!(
        "{}/answers.json",
        tests_path
    )) {
        None => {
            println!("Failed to load tests from {}\n", tests_path);
            return;
        }
        Some(tests) => tests,
    };

    let results: Vec<TestStatus> = tests
        .iter()
        .enumerate()
        .map(|(i, test)| run_test(i, tests.len(), test, &tests_path))
        .collect();

    let (passed, failed): (Vec<_>, Vec<_>) = results
        .into_iter()
        .partition(|status| matches!(status, TestStatus::Passed));
    println!(
        "Passed: {}, Failed: {}\n",
        passed.len().to_string().green(),
        failed.len().to_string().red()
    );
}

fn main() {
    let exports_folder = Path::new("assets/exports");
    if exports_folder.exists() {
        std::fs::remove_dir_all(exports_folder).unwrap();
    }
    std::fs::create_dir_all(exports_folder).unwrap();

    tests("assets/tests");
}
