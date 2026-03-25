use clap::Parser;
use std::fs;
use std::io::{self, Write};
use std::path::PathBuf;
use base64::{engine::general_purpose::URL_SAFE, Engine as _};

mod config {
    use serde::{Deserialize, Serialize};
    use std::fs;
    use std::path::PathBuf;

    #[derive(Serialize, Deserialize, Default)]
    pub struct Credentials {
        pub username: Option<String>,
        pub password: Option<String>,
    }

    pub fn get_config_path() -> PathBuf {
        let mut path = dirs::config_dir().unwrap_or_else(|| PathBuf::from("."));
        path.push("gmd_uploader");
        fs::create_dir_all(&path).ok();
        path.push("credentials.json");
        path
    }

    pub fn load_credentials() -> Credentials {
        if let Ok(data) = fs::read_to_string(get_config_path()) {
            serde_json::from_str(&data).unwrap_or_default()
        } else {
            Credentials::default()
        }
    }

    pub fn save_credentials(username: &str, password: &str) {
        let creds = Credentials {
            username: Some(username.to_string()),
            password: Some(password.to_string()),
        };
        if let Ok(data) = serde_json::to_string_pretty(&creds) {
            let _ = fs::write(get_config_path(), data);
        }
    }
}

mod crypto {
    use base64::{engine::general_purpose::URL_SAFE_NO_PAD, Engine as _};
    use sha1::{Digest, Sha1};

    pub fn xor_cipher(input: &str, key: &str) -> String {
        let key_bytes = key.as_bytes();
        let input_bytes = input.as_bytes();
        let out: Vec<u8> = input_bytes
            .iter()
            .enumerate()
            .map(|(i, &b)| b ^ key_bytes[i % key_bytes.len()])
            .collect();
        hex::encode(out)
    }

    pub fn generate_upload_seed(data: &str, chars: usize) -> String {
        if data.len() < chars {
            return data.to_string();
        }
        let step = data.len() / chars;
        let data_chars: Vec<char> = data.chars().collect();
        (0..chars).map(|i| data_chars[i * step]).collect()
    }

    pub fn generate_chk(values: &[&str], key: &str, salt: &str) -> String {
        let mut string = values.join("");
        string.push_str(salt);
        let hash = format!("{:x}", Sha1::digest(string.as_bytes()));
        let xored = xor_cipher(&hash, key);
        let bytes = hex::decode(xored).unwrap_or_default();
        URL_SAFE_NO_PAD.encode(bytes)
    }

    pub fn generate_seed(str_val: &str) -> String {
        let seed = generate_upload_seed(str_val, 50);
        generate_chk(&[&seed], "41274", "xI25fpAapCQg") + "=="
    }

    pub fn generate_gjp2(password: &str) -> String {
        let combined = format!("{}mI29fmAnxgTs", password);
        format!("{:x}", Sha1::digest(combined.as_bytes()))
    }
}

mod gmd {
    use roxmltree::Document;

    pub fn get_value<'a>(doc: &'a Document, key: &str) -> Option<&'a str> {
        for node in doc.descendants().filter(|n| n.is_element() && n.has_tag_name("k")) {
            if node.text().map(str::trim) == Some(key) {
                let mut sibling = node.next_sibling();

                while let Some(n) = sibling {
                    if n.is_element() {
                        return n.text().map(str::trim);
                    }
                    sibling = n.next_sibling();
                }
            }
        }

        None
    }
}

mod api {
    use crate::crypto;
    use base64::{engine::general_purpose::URL_SAFE_NO_PAD, Engine as _};
    use reqwest::Client;
    use std::collections::HashMap;

    pub async fn get_account_id(username: &str) -> Result<i32, Box<dyn std::error::Error>> {
        let client = Client::new();
        let mut form = HashMap::new();
        form.insert("secret", "Wmfd2893gb7");
        form.insert("str", username);

        let res = client
            .post("https://www.boomlings.com/database/getGJUsers20.php")
            .form(&form)
            .send()
            .await?
            .text()
            .await?;

        let parts: Vec<&str> = res.split('|').next().unwrap_or("").split(':').collect();
        for i in (0..parts.len()).step_by(2) {
            if parts[i] == "16" && i + 1 < parts.len() {
                return Ok(parts[i + 1].parse()?);
            }
        }
        Err("Account not found".into())
    }

    #[allow(clippy::too_many_arguments)]
    pub async fn upload_level(
        username: &str, password: &str, levelname: &str, leveldesc: &str, lvlstr: &str,
        audio_track: i32, song_id: i32, ver: i32, unlisted: i32, level_version: i32,
        objects: i32, level_id: i32, level_length: i32,
    ) -> Result<String, Box<dyn std::error::Error>> {
        let aid = get_account_id(username).await?;
        let gjp2 = crypto::generate_gjp2(password);
        let seed2 = crypto::generate_seed(lvlstr);
        
        let encoded_desc = URL_SAFE_NO_PAD.encode(leveldesc.as_bytes());

        let mut form = HashMap::new();
        form.insert("gameVersion".to_string(), ver.to_string());
        form.insert("accountID".to_string(), aid.to_string());
        form.insert("gjp2".to_string(), gjp2);
        form.insert("userName".to_string(), username.to_string());
        form.insert("levelID".to_string(), level_id.to_string());
        form.insert("levelName".to_string(), levelname.to_string());
        form.insert("levelDesc".to_string(), encoded_desc);
        form.insert("levelVersion".to_string(), level_version.to_string());
        form.insert("levelLength".to_string(), level_length.to_string());
        form.insert("audioTrack".to_string(), audio_track.to_string());
        form.insert("auto".to_string(), "0".to_string());
        form.insert("password".to_string(), "0".to_string());
        form.insert("original".to_string(), "0".to_string());
        form.insert("twoPlayer".to_string(), "0".to_string());
        form.insert("songID".to_string(), song_id.to_string());
        form.insert("objects".to_string(), objects.to_string());
        form.insert("coins".to_string(), "0".to_string());
        form.insert("requestedStars".to_string(), "0".to_string());
        form.insert("unlisted".to_string(), unlisted.to_string());
        form.insert("ldm".to_string(), "0".to_string());
        form.insert("levelString".to_string(), lvlstr.to_string());
        form.insert("seed2".to_string(), seed2);
        form.insert("secret".to_string(), "Wmfd2893gb7".to_string());

        let client = Client::new();
        let res = client
            .post("https://www.boomlings.com/database/uploadGJLevel21.php")
            .form(&form)
            .send()
            .await?
            .text()
            .await?;

        Ok(res)
    }
}

#[derive(Parser, Debug)]
#[command(author, version, about = "Upload a level to Geometry Dash server", long_about = None)]
struct Args {
    #[arg(short, long)]
    levelname: Option<String>,
    #[arg(short, long)]
    description: Option<String>,
    #[arg(long, default_value_t = 0)]
    id: i32,
    #[arg(short = 'v', long = "gameversion", default_value_t = 22)]
    gameversion: i32,
    #[arg(long, default_value_t = 1)]
    levelversion: i32,
    #[arg(long)]
    gmd: String,
    #[arg(long)]
    songid: Option<i32>,
    #[arg(long)]
    username: Option<String>,
    #[arg(long)]
    password: Option<String>,
    #[arg(short, long, default_value_t = 0)]
    mode: i32,
    #[arg(short = 'L', long = "level_length", default_value_t = 0)]
    level_length: i32,
}

#[tokio::main]
async fn main() {
    let args = Args::parse();
    let creds = config::load_credentials();
    
    let username = if let Some(u) = args.username.or(creds.username) {
        u
    } else {
        print!("enter Geometry Dash Username: ");
        io::stdout().flush().unwrap();
        let mut input = String::new();
        io::stdin().read_line(&mut input).expect("failed to read username");
        input.trim().to_string()
    };

    let password = if let Some(p) = args.password.or(creds.password) {
        p
    } else {
        rpassword::prompt_password("enter Account Password: ").expect("failed to read password")
    };

    let saved_creds = config::load_credentials();
    if saved_creds.username.is_none() || saved_creds.password.is_none() {
        print!("save account for future use? (y/n): ");
        io::stdout().flush().unwrap();
        let mut confirm = String::new();
        io::stdin().read_line(&mut confirm).ok();
        if confirm.trim().to_lowercase() == "y" {
            config::save_credentials(&username, &password);
            println!("account saved to local config.");
        }
    }

    // validate gmd
    if !args.gmd.to_lowercase().ends_with(".gmd") {
        eprintln!("Error: '{}' is not a .gmd file.", args.gmd);
        return;
    }

    let xml_content = match fs::read_to_string(&args.gmd) {
        Ok(c) => c,
        Err(e) => {
            eprintln!("Error reading file: {}", e);
            return;
        }
    };

    let doc = match roxmltree::Document::parse(&xml_content) {
        Ok(d) => d,
        Err(e) => {
            eprintln!("Error parsing XML structure: {}", e);
            return;
        }
    };

    let levelname = args.levelname.unwrap_or_else(|| {
    gmd::get_value(&doc, "k2")
        .unwrap_or("Unnamed Level")
        .to_string()
    });

    let raw_desc = gmd::get_value(&doc, "k3").unwrap_or("");
    let description = args.description.unwrap_or_else(|| {
    let mut s = raw_desc.replace('-', "+").replace('_', "/");
    while s.len() % 4 != 0 {
        s.push('=');
    }

    base64::engine::general_purpose::STANDARD
        .decode(s)
        .ok()
        .and_then(|bytes| String::from_utf8(bytes).ok())
        .unwrap_or_default()
    });

    let songid = args.songid.unwrap_or_else(|| {
        gmd::get_value(&doc, "k45").and_then(|v| v.parse().ok()).unwrap_or(0)
    });

    let level_id = if args.id == 0 { 
        gmd::get_value(&doc, "k1").and_then(|v| v.parse().ok()).unwrap_or(0) 
    } else { 
        args.id 
    };
    
    let lvlstr = match gmd::get_value(&doc, "k4") {
        Some(s) => s,
        None => {
            eprintln!("Error: Key 'k4' (Level String) not found in GMD file.");
            return;
        }
    };

    let objects: i32 = gmd::get_value(&doc, "k48").and_then(|v| v.parse().ok()).unwrap_or(1);

    println!("Name: {}", levelname);
    
    match api::upload_level(
        &username, &password, &levelname, &description, lvlstr,
        0, songid, args.gameversion, args.mode, args.levelversion,
        objects, level_id, args.level_length,
    ).await {
        Ok(res) => println!("\nSuccess! >_<\nServer Response: {}", res),
        Err(e) => eprintln!("\nUpload failed: {}", e),
    }
}