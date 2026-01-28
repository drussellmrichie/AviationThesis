import sys
import streamlit as st
import testPlatform as tp
from threading import Thread
import threading

def ex():
    st.title("Aviation Experiment Platform")

    # --- Create persistent session state entries ---
    if "stop_event" not in st.session_state:
        st.session_state.stop_event = threading.Event()
    if "experiment_thread" not in st.session_state:
        st.session_state.experiment_thread = None
    if "experiment_name" not in st.session_state:
        st.session_state.experiment_name = None
    if "experiment_number" not in st.session_state:
        st.session_state.experiment_number = None

    # --- Button to start experiment ---
    def start_experiment():
        if st.session_state.experiment_thread is None or not st.session_state.experiment_thread.is_alive():
            st.session_state.stop_event.clear()
            t1 = Thread(target=tp.ex, args=(st.session_state.stop_event,st.session_state.experiment_name,st.session_state.experiment_number), daemon=True)
            t1.start()
            st.session_state.experiment_thread = t1
            st.success("Experiment started.")
        else:
            st.warning("Experiment already running.")

    # --- Button to interrupt experiment ---
    def stop_experiment():
        if st.session_state.experiment_thread and st.session_state.experiment_thread.is_alive():
            st.session_state.stop_event.set()
            st.warning("Stop signal sent.")
        else:
            st.info("No running experiment to stop.")


    # --- Buttons ---
    st.button("Start Experiment", on_click=start_experiment)
    st.button("Interrupt Experiment", on_click=stop_experiment)
    st.session_state.experiment_name = st.text_input("Experiment Title",)
    st.session_state.experiment_name = st.text_input("Experiment Number",)
    st.write(f"Current Experiment Title: {st.session_state.experiment_name}")
    st.write(f"Current Experiment Number: {st.session_state.experiment_number}")


    # st.title("Aviation Experiment Platform")
    # # st.write("Welcome to the Aviation Experiment Platform GUI.")
    # # st.write("This platform allows experimenters to configure and run aviation-related experiments with ease.")
    # # st.write("Please use the sidebar to navigate through different sections of the platform.")
    # stop_event = threading.Event()
    # stop_event.clear() 
    # t1 = Thread(target=tp.ex, args=(stop_event,))

    # st.button("Start Experiment",on_click=t1.start)
    # st.button("Interrupt Experiment",on_click=stop_event.set)



if __name__ == "__main__":
    ex()