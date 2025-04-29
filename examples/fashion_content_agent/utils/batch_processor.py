# Process the batch
for item in batch:
    try:
        # Process the item
        result = process_item(item)
        if result:
            # Update the item with the result
            item.update(result)
            # Set status to success
            item['status'] = 'success'
        else:
            item['status'] = 'failed'
    except Exception as e:
        item['status'] = 'failed'
        item['error'] = str(e)
        failed_items.append(item)
        continue
    
    processed_items.append(item) 