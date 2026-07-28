from __future__ import annotations

import pytest

from core.limits import SELECT_LABEL_LENGTH_MAX, SELECT_OPTIONS_MAX
from core.pagination import (
    ItemSelect,
    ListPageProvider,
    PageSizeError,
    PaginatorConfiguration,
)


ITEMS = [f'item-{index}' for index in range(30)]


@pytest.fixture
def provider() -> ListPageProvider:
    return ListPageProvider(ITEMS, 10)


@pytest.mark.parametrize('per_page', [-1, 0, SELECT_OPTIONS_MAX + 1])
def test_list_page_provider_rejects_page_size(per_page: int) -> None:
    with pytest.raises(PageSizeError):
        ListPageProvider(ITEMS, per_page)


def test_list_page_provider_total_items(provider: ListPageProvider) -> None:
    assert provider.total_items_get() == len(ITEMS)


@pytest.mark.parametrize(
    ('count', 'per_page', 'expected'),
    [
        (0, 25, 0),
        (1, 25, 1),
        (25, 25, 1),
        (26, 25, 2),
        (30, 10, 3),
        (31, 10, 4),
    ]
)
def test_list_page_provider_total_pages(count: int, per_page: int, expected: int) -> None:
    items = [f'item-{index}' for index in range(count)]

    provider = ListPageProvider(items, per_page)
    assert provider.total_pages_get() == expected


def test_list_page_provider_first_page(provider: ListPageProvider) -> None:
    result = provider.page_get(1)
    assert result == ITEMS[:10]


def test_list_page_provider_last_page(provider: ListPageProvider) -> None:
    result = provider.page_get(3)
    assert result == ITEMS[20:]


def test_list_page_provider_page_beyond_total(provider: ListPageProvider) -> None:
    result = provider.page_get(4)
    assert result == []


def test_item_select_truncates_label() -> None:
    label = 'a' * (SELECT_LABEL_LENGTH_MAX + 50)

    select = ItemSelect([label])
    assert select.options[0].label == label[:SELECT_LABEL_LENGTH_MAX]


def test_item_select_values_are_indices() -> None:
    select = ItemSelect(['first', 'second'])

    values = [option.value for option in select.options]
    assert values == ['0', '1']


def test_item_select_formats_items() -> None:
    select = ItemSelect([1, 2], item_format=lambda item: f'number {item}')

    labels = [option.label for option in select.options]
    assert labels == ['number 1', 'number 2']


def test_paginator_configuration_defaults() -> None:
    configuration = PaginatorConfiguration()

    assert configuration.per_page == SELECT_OPTIONS_MAX
    assert configuration.timeout == 180.0
    assert not configuration.delete_message_on_timeout
    assert not configuration.return_on_selection


@pytest.mark.parametrize('page', [-1, 0])
def test_list_page_provider_rejects_page_below_one(provider: ListPageProvider, page: int) -> None:
    assert provider.page_get(page) == []


def test_item_select_truncates_options() -> None:
    items = [f'item-{index}' for index in range(SELECT_OPTIONS_MAX + 10)]

    select = ItemSelect(items)
    assert len(select.options) == SELECT_OPTIONS_MAX
