import os
import cv2
import numpy as np
import streamlit as st
from moviepy.editor import VideoFileClip
from datetime import timedelta
import tempfile
import time

# Configuración inicial de la aplicación
st.set_page_config(layout="wide", page_title="Editor de Video Nacsport-like")

# Variables de estado
if 'video_loaded' not in st.session_state:
    st.session_state.video_loaded = False
if 'clips' not in st.session_state:
    st.session_state.clips = []
if 'current_frame' not in st.session_state:
    st.session_state.current_frame = 0
if 'playing' not in st.session_state:
    st.session_state.playing = False
if 'mark_in' not in st.session_state:
    st.session_state.mark_in = 0
if 'mark_out' not in st.session_state:
    st.session_state.mark_out = 0


# Funciones principales
def load_video(file):
    """Carga el video y extrae información relevante"""
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    tfile.write(file.read())

    video = cv2.VideoCapture(tfile.name)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = video.get(cv2.CAP_PROP_FPS)
    duration = total_frames / fps
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))

    st.session_state.video_info = {
        'path': tfile.name,
        'total_frames': total_frames,
        'fps': fps,
        'duration': duration,
        'width': width,
        'height': height,
        'video_capture': video
    }
    st.session_state.video_loaded = True
    st.session_state.current_frame = 0
    return video


def get_frame(video_capture, frame_number):
    """Obtiene un frame específico del video"""
    video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ret, frame = video_capture.read()
    if ret:
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return None


def add_clip(start_frame, end_frame):
    """Añade un nuevo clip a la lista"""
    clip = {
        'id': len(st.session_state.clips),
        'start_frame': start_frame,
        'end_frame': end_frame,
        'start_time': start_frame / st.session_state.video_info['fps'],
        'end_time': end_frame / st.session_state.video_info['fps']
    }
    st.session_state.clips.append(clip)


def export_clip(clip):
    """Exporta un clip como archivo de video separado"""
    video_path = st.session_state.video_info['path']
    output_path = f"clip_{clip['id']}.mp4"

    with VideoFileClip(video_path) as video:
        subclip = video.subclip(clip['start_time'], clip['end_time'])
        subclip.write_videofile(output_path, codec='libx264')

    return output_path


def format_time(seconds):
    """Formatea segundos a formato HH:MM:SS.mmm"""
    return str(timedelta(seconds=seconds))


# Interfaz de usuario
st.title("Editor de Video Profesional - Estilo Nacsport")

# Panel de carga de video
with st.sidebar:
    st.header("Cargar Video")
    video_file = st.file_uploader("Selecciona un archivo de video", type=['mp4', 'avi', 'mov'])

    if video_file and not st.session_state.video_loaded:
        load_video(video_file)
        st.success("Video cargado correctamente")

    if st.session_state.video_loaded:
        st.header("Controles")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⏮️ Inicio"):
                st.session_state.current_frame = 0
                st.session_state.playing = False
            if st.button("⏪ -10s"):
                frames_to_skip = int(10 * st.session_state.video_info['fps'])
                st.session_state.current_frame = max(0, st.session_state.current_frame - frames_to_skip)
                st.session_state.playing = False
        with col2:
            if st.button("⏹️ Detener"):
                st.session_state.playing = False
            if st.button("⏩ +10s"):
                frames_to_skip = int(10 * st.session_state.video_info['fps'])
                st.session_state.current_frame = min(
                    st.session_state.video_info['total_frames'] - 1,
                    st.session_state.current_frame + frames_to_skip
                )
                st.session_state.playing = False

        st.slider(
            "Posición",
            0,
            st.session_state.video_info['total_frames'] - 1,
            st.session_state.current_frame,
            key="frame_slider",
            on_change=lambda: setattr(st.session_state, 'current_frame', st.session_state.frame_slider)
        )

        col3, col4 = st.columns(2)
        with col3:
            if st.button("Mark In"):
                st.session_state.mark_in = st.session_state.current_frame
                st.success(f"Mark In establecido en frame {st.session_state.mark_in}")
        with col4:
            if st.button("Mark Out"):
                st.session_state.mark_out = st.session_state.current_frame
                st.success(f"Mark Out establecido en frame {st.session_state.mark_out}")

        if st.button("Añadir Clip"):
            if st.session_state.mark_in < st.session_state.mark_out:
                add_clip(st.session_state.mark_in, st.session_state.mark_out)
                st.success("Clip añadido!")
            else:
                st.error("Mark Out debe ser mayor que Mark In")

        if st.button("Reproducir/Pausa"):
            st.session_state.playing = not st.session_state.playing

# Panel principal de visualización
if st.session_state.video_loaded:
    col1, col2 = st.columns([3, 1])

    with col1:
        st.header("Visualización del Video")

        # Mostrar el frame actual
        frame_placeholder = st.empty()
        video_capture = st.session_state.video_info['video_capture']

        # Barra de progreso
        progress_bar = st.progress(0)

        # Información del frame actual
        current_time = st.session_state.current_frame / st.session_state.video_info['fps']
        st.write(f"Tiempo actual: {format_time(current_time)}")

        # Reproducción automática
        if st.session_state.playing:
            while st.session_state.playing and st.session_state.current_frame < st.session_state.video_info[
                'total_frames'] - 1:
                frame = get_frame(video_capture, st.session_state.current_frame)
                if frame is not None:
                    frame_placeholder.image(frame, use_column_width=True)
                    progress_bar.progress(st.session_state.current_frame / st.session_state.video_info['total_frames'])
                    st.session_state.current_frame += 1
                    st.session_state.frame_slider = st.session_state.current_frame
                    time.sleep(1 / st.session_state.video_info['fps'])
                else:
                    st.session_state.playing = False
        else:
            frame = get_frame(video_capture, st.session_state.current_frame)
            if frame is not None:
                frame_placeholder.image(frame, use_column_width=True)
                progress_bar.progress(st.session_state.current_frame / st.session_state.video_info['total_frames'])

    with col2:
        st.header("Clips Creados")

        if st.session_state.clips:
            for clip in st.session_state.clips:
                with st.expander(
                        f"Clip {clip['id']}: {format_time(clip['start_time'])} - {format_time(clip['end_time'])}"):
                    st.write(f"Duración: {format_time(clip['end_time'] - clip['start_time'])}")
                    st.write(f"Frames: {clip['start_frame']} - {clip['end_frame']}")
                    if st.button(f"Exportar Clip {clip['id']}"):
                        output_path = export_clip(clip)
                        st.success(f"Clip exportado como {output_path}")
                        with open(output_path, "rb") as f:
                            st.download_button(
                                label="Descargar Clip",
                                data=f,
                                file_name=f"clip_{clip['id']}.mp4",
                                mime="video/mp4"
                            )
        else:
            st.info("No hay clips creados todavía")

else:
    st.info("Por favor, carga un video para comenzar")
