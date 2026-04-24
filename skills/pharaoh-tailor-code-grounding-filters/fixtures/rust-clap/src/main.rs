use clap::Parser;
use serde::Deserialize;

#[derive(Parser)]
#[command(version, about)]
struct Cli {
    #[arg(long)]
    license_key: Option<String>,
}

#[derive(Deserialize)]
struct RunConfig {
    #[serde(default = "default_mode")]
    mode: String,
}

fn default_mode() -> String {
    "prod".to_string()
}

fn main() {
    let _cli = Cli::parse();
}
