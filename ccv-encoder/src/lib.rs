mod frame;
mod lowres;
mod utils;

#[pyo3::pymodule(gil_used = false)]
mod ccv {
    use crate::frame::{self, MonitorDisplay};
    use pyo3::{PyResult, exceptions::PyTypeError, prelude::*};
    use rayon::prelude::*;

    #[pyclass(frozen)]
    #[pyo3(name = "MonitorDisplay")]
    struct PyMonitorDisplay(MonitorDisplay);

    #[pymethods]
    impl PyMonitorDisplay {
        #[new]
        fn new(grid: (u32, u32), monitor: (u32, u32), margin: (u32, u32, u32, u32)) -> Self {
            PyMonitorDisplay(MonitorDisplay {
                rows: grid.0,
                columns: grid.1,
                monitor_width: monitor.0,
                monitor_height: monitor.1,

                margin_left: margin.0,
                margin_top: margin.1,
                margin_right: margin.2,
                margin_bottom: margin.3,
            })
        }
    }

    #[pyclass(frozen)]
    #[pyo3(name = "Image")]
    struct Image {
        width: u32,
        height: u32,
        data: Vec<u8>,
    }

    #[pymethods]
    impl Image {
        #[new]
        fn new(width: u32, height: u32, data: Vec<u8>) -> Self {
            Image {
                width,
                height,
                data,
            }
        }
    }

    type RgbImage = image::ImageBuffer<image::Rgb<u8>, Vec<u8>>;
    impl Image {
        fn convert(&self) -> PyResult<RgbImage> {
            image::ImageBuffer::from_raw(self.width, self.height, self.data.clone())
                .ok_or(PyTypeError::new_err("Failed to Loading Image"))
        }
    }

    #[pyfunction]
    #[pyo3(name = "encode_frame")]
    fn encode_frame(images: Py<Image>, display: Py<PyMonitorDisplay>) -> PyResult<Vec<u8>> {
        let display = &display.get().0;
        let img = images.get().convert()?;

        let result = frame::encode_lowres_frame(&img, display);
        result.map_err(|err| PyTypeError::new_err(err.to_string()))
    }

    #[pyfunction]
    #[pyo3(name = "encode_frames")]
    fn encode_frames(
        images: Vec<Py<Image>>,
        display: Py<PyMonitorDisplay>,
    ) -> PyResult<Vec<Vec<u8>>> {
        let display = &display.get().0;
        let images: PyResult<Vec<RgbImage>> = images.iter().map(|v| v.get().convert()).collect();
        let results: Result<Vec<Vec<u8>>, frame::EncodeError> = images?
            .into_par_iter()
            .map(|img| frame::encode_lowres_frame(&img, display))
            .collect();
        results.map_err(|err| PyTypeError::new_err(err.to_string()))
    }
}
