
import os
import numpy as np
import tensorflow as tf

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
modelFullPath = os.path.join(SITE_ROOT, "static/data", "output_sopp_graph.pb")
labelsFullPath = os.path.join(SITE_ROOT, "static/data", "output_sopp_labels.txt")


def create_graph():
    """Creates a graph from saved GraphDef file and returns a saver."""
    # Creates graph from saved graph_def.pb.
    with tf.gfile.FastGFile(modelFullPath, 'rb') as f:
        graph_def = tf.GraphDef()
        graph_def.ParseFromString(f.read())
        _ = tf.import_graph_def(graph_def, name='')


def run_inference_on_image(image):
    answer = None
    imagePath = image

    if not tf.gfile.Exists(imagePath):
        tf.logging.fatal('File does not exist %s', imagePath)
        return answer

    image_data = tf.gfile.FastGFile(imagePath, 'rb').read()

    # Creates graph from saved GraphDef.
    create_graph()

    with tf.Session() as sess:

        softmax_tensor = sess.graph.get_tensor_by_name('final_result:0')
        predictions = sess.run(softmax_tensor,
                               {'DecodeJpeg/contents:0': image_data})
        predictions = np.squeeze(predictions)

        top_k = predictions.argsort()[-5:][::-1]  # Getting top 5 predictions
        f = open(labelsFullPath, 'rb')
        lines = f.readlines()
        labels = [str(w).replace("\n", "") for w in lines]
        predictions_list = []
        for node_id in top_k:
            prediction = []
            prediction.append(labels[node_id].replace("b'","").replace("\\n","").replace("'","").replace("\\r", ""))
            prediction.append(predictions[node_id]*100)
            predictions_list.append(prediction)

        return predictions_list
