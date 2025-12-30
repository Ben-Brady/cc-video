use std::fmt;

pub struct MonitorDisplay {
    pub rows: u32,
    pub columns: u32,
    pub monitor_width: u32,
    pub monitor_height: u32,

    pub margin_left: u32,
    pub margin_right: u32,
    pub margin_top: u32,
    pub margin_bottom: u32,
}

pub struct Resolution {
    pub width: u32,
    pub height: u32,
}

#[derive(Debug)]
pub enum EncodeError {
    ImageLoad,
    ImageTooBig,
    ImageIncorrectSize,
    InternalError,
}

impl fmt::Display for EncodeError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match *self {
            EncodeError::ImageIncorrectSize => write!(f, "Image was incorrect size when encoding"),
            EncodeError::ImageLoad => write!(f, "Image loading failed"),
            EncodeError::ImageTooBig => write!(f, "Image was too big to encode"),
            EncodeError::InternalError => write!(f, "Internal Encoding Error"),
        }
    }
}
