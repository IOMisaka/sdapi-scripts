import launch

if not launch.is_installed("diffusers"):
    launch.run_pip(f"install diffusers", "diffusers")

import torch
from diffusers.pipelines.stable_diffusion.safety_checker import StableDiffusionSafetyChecker
from transformers import AutoFeatureExtractor
from PIL import Image
import numpy as np
from modules import scripts, shared
from modules.processing import process_images
import gradio as gr

safety_model_id = "CompVis/stable-diffusion-safety-checker"
safety_feature_extractor = None
safety_checker = None

def pil_to_numpy(images):
    n_images = [np.array(image,dtype=float) for image in images]
    return n_images
# check and replace nsfw content
def check_safety(x_image):
    global safety_feature_extractor, safety_checker

    if safety_feature_extractor is None:
        safety_feature_extractor = AutoFeatureExtractor.from_pretrained(safety_model_id)
        safety_checker = StableDiffusionSafetyChecker.from_pretrained(safety_model_id)

    safety_checker_input = safety_feature_extractor(x_image, return_tensors="pt")
    _, has_nsfw_concepts = safety_checker(images=pil_to_numpy(x_image), clip_input=safety_checker_input.pixel_values)
    return has_nsfw_concepts

def mosaic(img:Image):
    s = img.size
    img.thumbnail((17,17))
    img = img.resize(s,Image.NEAREST)
    return img

class CensorScript(scripts.Script):
    def title(self):
        return "CensorScript"

    def show(self, is_img2img):
        return True

    def ui(self, is_img2img):
        nsfw_check = gr.Checkbox(False, label="NSFW check")
        nsfw_mosaic = gr.Checkbox(False, label="NSFW with mosaic")
        return [nsfw_check,nsfw_mosaic]

    def run(self,p,nsfw_check,nsfw_mosaic):
        print("NSFW check:",nsfw_check," mosaic:",nsfw_mosaic)
        proc = process_images(p)
        if not nsfw_check:
            return proc
        #nsfw check
        has_nsfw_concepts = check_safety(proc.images)
        print("NSFW results:",has_nsfw_concepts)
        proc.extra_generation_params['nsfw'] = has_nsfw_concepts
        for index,nsfw in enumerate(has_nsfw_concepts):
            if nsfw and nsfw_mosaic:
                proc.images[index] = mosaic(proc.images[index])
        return proc