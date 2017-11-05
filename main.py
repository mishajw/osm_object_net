from object_net import object_net_components
from object_net import object_net_writer
from object_net import padder
import configargparse
import item
import logging
import osm_map
import tensorflow as tf
import tf_utils


def main():
    # Handle program arguments
    parser = configargparse.ArgParser()
    parser.add_argument(
        "--config", is_config_file=True, default="./osm_object_net.ini", help="Path of ini configuration file")
    parser.add_argument("--hidden_vector_length", type=int, default=64)
    parser.add_argument("--fully_connected_sizes", type=str, default="256,256")
    parser.add_argument("--osm_path", type=str, help="The path of the .osm file to parse", default="data/map.osm")
    tf_utils.generic_runner.GenericRunner.add_arguments(parser)
    tf_utils.data_holder.add_arguments(parser)
    args = parser.parse_args()

    # Generate data
    print("Generating data...")
    osm_type = item.get_object_net_type()
    _osm_map = osm_map.parse(args.osm_path)
    items = [i.get_dict() for i in item.parse(_osm_map)]
    state_output_pairs = [list(osm_type.get_state_output_pairs(items))] * 100
    padded_data = padder.PaddedData.from_unpadded(state_output_pairs)
    data_holder = tf_utils.data_holder.DataHolder(
        args,
        get_data_fn=lambda i: padded_data[i],
        data_length=len(padded_data))
    print("Done")

    # Define graph
    truth_padded_data = padder.PlaceholderPaddedData()

    with tf.variable_scope("truth_initial_hidden_vector_input"):
        truth_initial_hidden_vector_input = tf.random_uniform([truth_padded_data.batch_size, 32])

    def get_object_net_writer(training: bool) -> object_net_writer.ObjectNetWriter:
        return object_net_writer.ObjectNetWriter(
            truth_padded_data,
            truth_initial_hidden_vector_input,
            object_type=osm_type,
            training=training,
            hidden_vector_network=object_net_components.FullyConnectedHiddenVectorNetwork(
                layer_sizes=[128] * 2,
                hidden_vector_size=args.hidden_vector_length,
                hidden_vector_combiner=object_net_components.AdditionHiddenVectorCombiner()))

    object_net = get_object_net_writer(training=True)
    object_net_test = get_object_net_writer(training=False)

    tf.summary.scalar("osm_object_net/cost", object_net.cost)
    optimizer = tf.train.AdamOptimizer().minimize(object_net.cost)

    # Run training
    def train_step(session, step, training_input, all_summaries, summary_writer):
        c, _, all_summaries = session.run(
            [object_net.cost, optimizer, all_summaries],
            truth_padded_data.get_feed_dict(training_input))

        print(f"Train step {step}: {c}")

        summary_writer.add_summary(all_summaries, step)

    def test_step(session, step, testing_input, all_summaries, summary_writer):
        cost_result, all_summaries = session.run(
            [object_net.cost, all_summaries],
            truth_padded_data.get_feed_dict(testing_input))

        summary_writer.add_summary(all_summaries, step)

        print("Test cost at step %d: %f" % (step, cost_result))

        show_examples(session, testing_input)

    def show_examples(session, model_input):
        # Limit to 10 inputs
        model_input = [x[:10] for x in model_input]

        generated_states_padded, \
            generated_outputs_padded, \
            generated_outputs_counts_padded, \
            generated_step_counts, \
            current_initial_hidden_vector_input = session.run(
                [
                    object_net_test.generated_states_padded,
                    object_net_test.generated_outputs_padded,
                    object_net_test.generated_outputs_counts_padded,
                    object_net_test.generated_step_counts,
                    truth_initial_hidden_vector_input],
                truth_padded_data.get_feed_dict(model_input))

        copied_testing_input = padder.PaddedData(
            generated_step_counts, generated_outputs_counts_padded, generated_states_padded, generated_outputs_padded)
        unpadded = padder.unpad(copied_testing_input)

        def try_array_to_items(_array):
            try:
                return osm_type.get_value_from_state_output_pairs(_array)
            except StopIteration:
                return []

        print("Items:")
        for tree in [try_array_to_items(array) for array in unpadded]:
            print(tree)

        print("Raw unpadded data:")
        [print(list(unpadded)) for unpadded in padder.unpad(copied_testing_input)]

        print("Lengths:")
        print([len(list(unpadded)) for unpadded in padder.unpad(copied_testing_input)])

    args.batch_size = 1
    runner = tf_utils.generic_runner.GenericRunner.from_args(args, "osm_object_net")
    runner.set_data_holder(data_holder)
    runner.set_test_step(test_step)
    runner.set_train_step(train_step)
    runner.run()


if __name__ == "__main__":
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)
    main()
