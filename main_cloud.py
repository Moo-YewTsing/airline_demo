import time
from airline_demo.ml import preprocess
from airline_demo.ml.trainer import task
from airline_demo.ml.trainer import model

import tensorflow_transform as tft

if __name__ == "__main__":
    ARGV1 = [
        '--train-data-file=gs://linelineline/for_ai/train*',
        '--test-data-file=gs://linelineline/for_ai/eval*',
        '--root-train-data-out=train',
        '--root-test-data-out=eval',
        '--working-dir=gs://linelineline/work_dir',
        '--runner=DataflowRunner',
        '--region=us-central1',
        f'--job_name=preprocess{int(time.time())}',
        '--setup_file=./setup.py',
        '--flexrs_goal=COST_OPTIMIZED',
        '--project=airlinegcp'
    ]
    preprocess.main(ARGV1)

    # ARGV2 = [
    #     '--train_files=gs://linelineline/work_dir/train*',
    #     '--tf_transform_dir=gs://linelineline/work_dir',
    #     '--output_dir=models',
    #     '--eval_files=gs://linelineline/work_dir/eval*',
    #     '--train_steps=2000',
        # '--tag=flights'
        #  '--job_dir',
    # ]

    # task.main(ARGV2)
    
    # tf_transform_output = tft.TFTransformOutput('work_dir')
    # print(model.eval_input_receiver_fn(tf_transform_output))
    # fn = 'work_dir/train*'
    # print(model.get_raw_feature_spec())
    # print(model.input_fn(fn, tf_transform_output))