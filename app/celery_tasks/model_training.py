import pandas as pd
import tensorflow as tf
import tensorflow_probability as tfp


from meridian import constants
from meridian.data import load
from meridian.model import model
from meridian.model import spec
from meridian.model import prior_distribution
from meridian.analysis import visualizer
from psutil import virtual_memory

from app.celery_tasks.celery import celery


@celery.task(timeout=3600)
def training(
    raw_data: dict
):

    df = pd.DataFrame(raw_data)

    # check if GPU is available
    ram_gb = virtual_memory().total / 1e9
    print('Your runtime has {:.1f} gigabytes of available RAM\n'.format(ram_gb))
    print("Num GPUs Available: ", len(tf.config.experimental.list_physical_devices('GPU')))
    print("Num CPUs Available: ", len(tf.config.experimental.list_physical_devices('CPU')))

    coord_to_columns = load.CoordToColumns(
        time='time',
        geo='geo',
        controls=['GQV', 'Competitor_Sales'],
        population='population',
        kpi='conversions',
        revenue_per_kpi='revenue_per_conversion',
        media=[
            'Channel0_impression',
            'Channel1_impression',
            'Channel2_impression',
            'Channel3_impression',
            'Channel4_impression',
        ],
        media_spend=[
            'Channel0_spend',
            'Channel1_spend',
            'Channel2_spend',
            'Channel3_spend',
            'Channel4_spend',
        ],
        organic_media=['Organic_channel0_impression'],
        non_media_treatments=['Promo'],
    )
    print(f'{coord_to_columns}')

    correct_media_to_channel = {
        'Channel0_impression': 'Channel_0',
        'Channel1_impression': 'Channel_1',
        'Channel2_impression': 'Channel_2',
        'Channel3_impression': 'Channel_3',
        'Channel4_impression': 'Channel_4',
    }
    correct_media_spend_to_channel = {
        'Channel0_spend': 'Channel_0',
        'Channel1_spend': 'Channel_1',
        'Channel2_spend': 'Channel_2',
        'Channel3_spend': 'Channel_3',
        'Channel4_spend': 'Channel_4',
    }

    loader = load.DataFrameDataLoader(
        df=df,
        kpi_type='non_revenue',
        coord_to_columns=coord_to_columns,
        media_to_channel=correct_media_to_channel,
        media_spend_to_channel=correct_media_spend_to_channel,
    )
    data = loader.load()
    print(f'{data.controls}')

    roi_mu = 0.2     # Mu for ROI prior for each media channel.
    roi_sigma = 0.9  # Sigma for ROI prior for each media channel.
    prior = prior_distribution.PriorDistribution(
        roi_m=tfp.distributions.LogNormal(roi_mu, roi_sigma, name=constants.ROI_M)
    )
    model_spec = spec.ModelSpec(prior=prior)

    mmm = model.Meridian(input_data=data, model_spec=model_spec)
    print(f'{mmm=}')

    mmm.sample_prior(200)
    print(f'BLOCK AFTER sample_prior(300)')
    mmm.sample_posterior(n_chains=2, n_adapt=100, n_burnin=100, n_keep=100, seed=1)
    print('END', 50 * '-----------')

    media_summary = visualizer.MediaSummary(mmm)
    r = media_summary.summary_table()
    print(r)
    print(type(r))
