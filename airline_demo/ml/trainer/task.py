import argparse
import os

import tensorflow as tf
import tensorflow_transform as tft
import tensorflow_model_analysis as tfma

try:
    from airline_demo.ml.trainer import model
except ImportError:
    from trainer import model

SERVING_MODEL_DIR = 'serving_model_dir'
EVAL_MODEL_DIR = 'eval_model_dir'

TRAIN_BATCH_SIZE = 1000
EVAL_BATCH_SIZE = 1000

def my_metric(labels, predictions):
    pred_values = predictions['logistic']
    return {'auc': tf.metrics.auc(labels, pred_values)}

def train_and_maybe_evaluate(hparams):
    """Run the training and evaluate using the high level API.

    Args:
        hparams: Holds hyperparameters used to train the model as name/value pairs.

    Returns:
        The estimator that was used for training (and maybe eval)
    """
    tf_transform_output = tft.TFTransformOutput(hparams.tf_transform_dir)
    tag = hparams.tag

    train_input = lambda: model.input_fn(
            hparams.train_files,
            tf_transform_output,
            batch_size=TRAIN_BATCH_SIZE
    )

    eval_input = lambda: model.input_fn(
            hparams.eval_files,
            tf_transform_output,
            batch_size=EVAL_BATCH_SIZE
    )

    train_spec = tf.estimator.TrainSpec(
            train_input, max_steps=hparams.train_steps)

    serving_receiver_fn = lambda: model.example_serving_receiver_fn(
            tf_transform_output)

    exporter = tf.estimator.FinalExporter(tag, serving_receiver_fn)
    eval_spec = tf.estimator.EvalSpec(
            eval_input,
            steps=hparams.eval_steps,
            exporters=[exporter],
            name='{}-eval'.format(tag))

    run_config = tf.estimator.RunConfig(
            # save_checkpoints_steps=999,
            keep_checkpoint_max=1)

    # serving_model_dir = os.path.join(hparams.output_dir, SERVING_MODEL_DIR)
    serving_model_dir = os.path.join(hparams.output_dir, 
                            '{}_serving'.format(hparams.first_dnn_layer_size))

    run_config = run_config.replace(model_dir=serving_model_dir)

    estimator = model.build_estimator(
            run_config,
            # Construct layers sizes with exponetial decay
            hidden_units=[
                    max(2, int(hparams.first_dnn_layer_size * hparams.dnn_decay_factor**i))
                    for i in range(hparams.num_dnn_layers)],
            wide=hparams.wide
            )

    estimator = tf.estimator.add_metrics(estimator, my_metric)

    tf.estimator.train_and_evaluate(estimator, train_spec, eval_spec)

    eval_input_receiver_fn = lambda: model.eval_input_receiver_fn(
            tf_transform_output)
    
    eval_model_dir = os.path.join(hparams.output_dir, 
                            '{}_eval'.format(hparams.first_dnn_layer_size))
    tfma.export.export_eval_savedmodel(
        estimator=estimator, export_dir_base=eval_model_dir,
        eval_input_receiver_fn=eval_input_receiver_fn)

    return estimator

def main(argv=None):
    parser = argparse.ArgumentParser()
    # Input Arguments
    parser.add_argument(
            '--train_files',
            help='GCS or local paths to training data',
            nargs='+',
            required=True)

    parser.add_argument(
            '--tf_transform_dir',
            help='Tf-transform directory with model from preprocessing step',
            required=True)

    parser.add_argument(
            '--output_dir',
            help="""\
            Directory under which where the serving model (under /serving_model_dir)\
            and the tf-mode-analysis model (under /eval_model_dir) will be written\
            """,
            required=True)

    parser.add_argument(
            '--eval_files',
            help='GCS or local paths to evaluation data',
            nargs='+',
            required=True)
    # # Training arguments
    # parser.add_argument(
    #         '--job_dir',
    #         help='GCS location to write checkpoints and export models',
    #         required=True)

    # Argument to turn on all logging
    parser.add_argument(
            '--verbosity',
            choices=['DEBUG', 'ERROR', 'FATAL', 'INFO', 'WARN'],
            default='INFO',
    )
    # Experiment arguments
    parser.add_argument(
            '--train_steps',
            help='Count of steps to run the training job for',
            required=True,
            type=int)
    parser.add_argument(
            '--eval_steps',
            help='Number of steps to run evalution for at each checkpoint',
            default=200,
            type=int)

    parser.add_argument(
            '--tag',
            default='flights',
    )

    parser.add_argument(
            '--first_dnn_layer_size',
            default=150,
            type=int
    )

    parser.add_argument(
            '--num_dnn_layers',
            default=4,
            type=int
    )

    parser.add_argument(
            '--dnn_decay_factor',
            default=1.0,
            type=float
    )

    parser.add_argument(
            '--wide',
            type=bool,
            default=True)

    args = parser.parse_args(argv)
    # Set python level verbosity
    tf.logging.set_verbosity(args.verbosity)
    hparams = args

    train_and_maybe_evaluate(hparams)

    # return estimator
if __name__ == "__main__":
    main()