use crate::frame::Resolution;
use crate::utils::{EncodeError, MonitorDisplay};
use image::imageops::resize;
use image::{DynamicImage, GenericImage, ImageBuffer, Rgb, RgbImage};
use quantette::{ImageBuf, PaletteSize};

pub fn encode_lowres_frame(
    img: &RgbImage,
    display: &MonitorDisplay,
) -> Result<Vec<u8>, EncodeError> {
    let columns = display.columns;
    let rows = display.rows;
    let monitor_count = (rows * columns) as usize;

    let render_size = (display.monitor_height * display.monitor_width * 2) as usize;
    let per_monitor_size = 3 + (3 * 16) + render_size;
    let output_size = 3 + (per_monitor_size * monitor_count);
    let mut output = Vec::<u8>::with_capacity(output_size);

    output.push(monitor_count.try_into().or(Err(EncodeError::ImageTooBig))?);
    output.push(columns.try_into().or(Err(EncodeError::ImageTooBig))?);
    output.push(rows.try_into().or(Err(EncodeError::ImageTooBig))?);

    let img = place_img_on_background(img, display)?;
    let monitors = split_into_monitors(img.into(), display)?
        .into_iter()
        .map(|monitor| encode_monitor(monitor, display))
        .collect::<Result<Vec<Vec<u8>>, EncodeError>>()?;

    output.extend(monitors.concat());
    assert_eq!(output.len(), output_size);
    Ok(output)
}

fn place_img_on_background(
    img: &RgbImage,
    display: &MonitorDisplay,
) -> Result<RgbImage, EncodeError> {
    let tile = calculate_tile_size(display);
    let mut background = RgbImage::new(
        tile.width * display.columns, //
        tile.height * display.rows,
    );

    let reduced_size = calculate_downscale(
        display,
        &Resolution {
            width: background.width(),
            height: background.height(),
        },
    );

    let img = resize(
        img,
        reduced_size.width,
        reduced_size.height,
        image::imageops::FilterType::Nearest,
    );
    background
        .copy_from(
            &img,
            (background.width() - img.width()) / 2,
            (background.height() - img.height()) / 2,
        )
        .or(Err(EncodeError::InternalError))?;

    Ok(background)
}

struct MonitorChunk {
    index: u32,
    img: ImageBuffer<Rgb<u8>, Vec<u8>>,
}

fn encode_monitor(monitor: MonitorChunk, display: &MonitorDisplay) -> Result<Vec<u8>, EncodeError> {
    let palette_size: u32 = 3 * 16;
    let render_size = display.monitor_width * display.monitor_height * 2;
    let output_size = (3 + palette_size + render_size) as usize;
    let mut output = Vec::<u8>::with_capacity(output_size);

    let index = monitor.index + 1;
    output.push(index.try_into().or(Err(EncodeError::ImageTooBig))?);
    let width = display.monitor_width;
    output.push(width.try_into().or(Err(EncodeError::ImageTooBig))?);
    let height = display.monitor_height;
    output.push(height.try_into().or(Err(EncodeError::ImageTooBig))?);

    let img_buf = ImageBuf::try_from(monitor.img).or(Err(EncodeError::ImageLoad))?;
    let (palette, pixels) = quantette::Pipeline::new()
        .palette_size(PaletteSize::from_u8_clamped(16))
        .ditherer(None)
        .parallel(true)
        .input_image(img_buf.as_ref())
        .output_srgb8_indexed_image()
        .into_parts();

    let mut palette_colors = palette.into_iter();
    // ensure palette is 48 bytes long
    for _ in 0..16 {
        let rgb_values = match palette_colors.next() {
            Some(pixel) => [pixel.red, pixel.green, pixel.blue],
            None => [0, 0, 0],
        };
        output.extend(rgb_values);
    }
    debug_assert_eq!(output.len(), 3 + (16 * 3));

    let text: Vec<u8> = std::iter::repeat_n(135, display.monitor_width as usize).collect();

    let mut lines = pixels.chunks(display.monitor_width as usize);
    while lines.len() >= 2 {
        let first_line = lines.next().ok_or(EncodeError::InternalError)?;
        let second_line = lines.next().ok_or(EncodeError::InternalError)?;
        let colors: Vec<u8> = [first_line, second_line]
            .concat()
            .chunks(2)
            .map(|nums| nums[1] + (nums[0] << 4))
            .collect();

        debug_assert_eq!(text.len(), display.monitor_width as usize);
        debug_assert_eq!(colors.len(), display.monitor_width as usize);
        output.extend(text.clone());
        output.extend(colors);
    }

    assert_eq!(output.len(), output_size);
    Ok(output)
}

fn split_into_monitors(
    img: DynamicImage,
    display: &MonitorDisplay,
) -> Result<Vec<MonitorChunk>, EncodeError> {
    let tile = calculate_tile_size(display);

    if !img.width().is_multiple_of(tile.width) || !img.height().is_multiple_of(tile.height) {
        return Err(EncodeError::ImageIncorrectSize);
    }

    let mut chunks = Vec::<MonitorChunk>::new();

    let mut index: u32 = 0;
    for y in 0..display.rows {
        for x in 0..display.columns {
            let left = (x * tile.width) + display.margin_left;
            let top = (y * tile.height) + display.margin_top;
            let img = img
                .crop_imm(left, top, display.monitor_width, display.monitor_height * 2)
                .into_rgb8();
            chunks.push(MonitorChunk { index, img });
            index += 1;
        }
    }

    assert_eq!(chunks.len(), (display.rows * display.columns) as usize);
    Ok(chunks)
}

fn calculate_downscale(display: &MonitorDisplay, max: &Resolution) -> Resolution {
    let tile = calculate_tile_size(display);
    let width = (tile.width * display.columns) as f64;
    let height = (tile.height * display.rows) as f64;

    let w_ratio = max.width as f64 / width;
    let h_ratio = max.height as f64 / height;
    let ratio = if w_ratio < h_ratio { w_ratio } else { h_ratio };

    Resolution {
        width: (width * ratio).floor() as u32,
        height: (height * ratio).floor() as u32,
    }
}

fn calculate_tile_size(display: &MonitorDisplay) -> Resolution {
    let tile_width = display.monitor_width + display.margin_left + display.margin_right;
    let tile_height = (display.monitor_height * 2) + display.margin_top + display.margin_bottom;
    Resolution {
        width: tile_width,
        height: tile_height,
    }
}
